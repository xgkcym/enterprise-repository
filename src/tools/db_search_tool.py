from typing import Iterable

from sqlmodel import func, select

from core.custom_types import DocumentMetadata
from src.database.postgres import get_sync_session
from service.models.department import DepartmentModel
from service.models.file import FileModel
from service.models.role import RoleModel
from service.models.role_department import RoleDepartmentModel
from service.models.users import UserModel
from src.types.db_search_type import DBQueryKind, DBSearchContext
from src.types.rag_type import DocumentInfo, RAGResult


def _normalize_query_text(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip()).lower()


def _looks_like_count_query(text: str) -> bool:
    markers = ["多少", "数量", "几个", "几条", "count", "how many", "总数"]
    return any(marker in text for marker in markers)


def _infer_db_query_kind(context: DBSearchContext) -> DBQueryKind:
    text = _normalize_query_text(context.query or "", context.rewritten_query or "")

    if ("角色" in text or "role" in text) and ("部门" in text or "权限" in text or "scope" in text):
        return "role_department_scope"
    if ("可访问" in text or "权限" in text or "部门" in text) and ("部门" in text or "department" in text):
        return "accessible_departments"
    if ("我" in text or "我的" in text or "my" in text) and ("上传" in text or "文件" in text or "file" in text):
        return "my_uploaded_files" if not _looks_like_count_query(text) else "accessible_file_count"
    if ("最近" in text or "最新" in text or "recent" in text or "latest" in text) and (
        "文件" in text or "file" in text
    ):
        return "recent_accessible_files"
    if ("文件" in text or "file" in text) and _looks_like_count_query(text):
        return "accessible_file_count"
    return "unsupported"


def _build_result(
    *,
    answer: str,
    documents: list[DocumentInfo] | None = None,
    citations: list[str] | None = None,
    evidence_summary: str | None = None,
    is_sufficient: bool,
    fail_reason=None,
    diagnostics: list[str] | None = None,
    success: bool = True,
) -> RAGResult:
    return RAGResult(
        success=success,
        name="db_search",
        answer=answer,
        evidence_summary=evidence_summary if evidence_summary is not None else answer,
        documents=documents or [],
        citations=citations or [],
        is_sufficient=is_sufficient,
        fail_reason=fail_reason,
        diagnostics=diagnostics or [],
    )


def _make_doc(node_id: str, content: str, *, file_name: str = "", file_path: str = "", section_title: str = "") -> DocumentInfo:
    return DocumentInfo(
        node_id=node_id,
        content=content,
        metadata=DocumentMetadata(
            file_name=file_name or node_id,
            file_path=file_path,
            file_type="db_record",
            source="db_search",
            section_title=section_title,
        ),
    )


def _dedupe_docs(documents: Iterable[DocumentInfo]) -> list[DocumentInfo]:
    merged = []
    seen = set()
    for doc in documents:
        if not doc.node_id or doc.node_id in seen:
            continue
        seen.add(doc.node_id)
        merged.append(doc)
    return merged


def _query_accessible_departments(context: DBSearchContext) -> tuple[str, list[DocumentInfo], list[str]]:
    if not context.allowed_department_ids:
        return "当前用户没有可访问的部门。", [], []

    with get_sync_session() as session:
        rows = session.exec(
            select(DepartmentModel).where(DepartmentModel.dept_id.in_(context.allowed_department_ids))
        ).all()

    documents = [
        _make_doc(
            f"db://department/{row.dept_id}",
            f"部门ID: {row.dept_id}\n部门名称: {row.dept_name}",
            file_name=row.dept_name,
            section_title="accessible_department",
        )
        for row in rows
    ]
    citations = [doc.node_id for doc in documents]
    names = [row.dept_name for row in rows]
    answer = "当前用户可访问的部门有：" + "、".join(names) if names else "当前用户没有可访问的部门。"
    return answer, documents, citations


def _query_accessible_file_count(context: DBSearchContext) -> tuple[str, list[DocumentInfo], list[str]]:
    if not context.allowed_department_ids:
        return "当前用户没有可访问的文件范围。", [], []

    with get_sync_session() as session:
        total = session.exec(
            select(func.count()).select_from(FileModel).where(
                FileModel.dept_id.in_(context.allowed_department_ids),
                FileModel.state != "0",
                FileModel.state != "4",
            )
        ).one()

    doc = _make_doc(
        "db://file/count/accessible",
        f"当前用户可访问文件总数: {total}",
        file_name="accessible_file_count",
        section_title="accessible_file_count",
    )
    answer = f"当前用户可访问的文件数量为 {total}。"
    return answer, [doc], [doc.node_id]


def _query_recent_accessible_files(context: DBSearchContext) -> tuple[str, list[DocumentInfo], list[str]]:
    if not context.allowed_department_ids:
        return "当前用户没有可访问的文件范围。", [], []

    limit = max(1, min(context.limit, 10))
    with get_sync_session() as session:
        rows = session.exec(
            select(FileModel).where(
                FileModel.dept_id.in_(context.allowed_department_ids),
                FileModel.state != "0",
                FileModel.state != "4",
            ).order_by(FileModel.create_time.desc()).limit(limit)
        ).all()

    documents = [
        _make_doc(
            f"db://file/{row.file_id}",
            "\n".join(
                [
                    f"文件ID: {row.file_id}",
                    f"文件名: {row.file_name}",
                    f"文件类型: {row.file_type}",
                    f"部门ID: {row.dept_id}",
                    f"上传用户ID: {row.user_id}",
                    f"创建时间: {row.create_time}",
                    f"文件路径: {row.file_path}",
                ]
            ),
            file_name=row.file_name,
            file_path=row.file_path,
            section_title="recent_accessible_file",
        )
        for row in rows
    ]
    citations = [doc.node_id for doc in documents]
    names = [row.file_name for row in rows]
    answer = "最近可访问的文件有：" + "、".join(names) if names else "当前没有可访问的最近文件。"
    return answer, documents, citations


def _query_my_uploaded_files(context: DBSearchContext) -> tuple[str, list[DocumentInfo], list[str]]:
    if context.user_id is None:
        return "缺少当前用户信息，无法查询个人上传文件。", [], []

    limit = max(1, min(context.limit, 10))
    with get_sync_session() as session:
        rows = session.exec(
            select(FileModel).where(
                FileModel.user_id == context.user_id,
                FileModel.state != "0",
                FileModel.state != "4",
            ).order_by(FileModel.create_time.desc()).limit(limit)
        ).all()

    documents = [
        _make_doc(
            f"db://file/{row.file_id}",
            "\n".join(
                [
                    f"文件ID: {row.file_id}",
                    f"文件名: {row.file_name}",
                    f"文件类型: {row.file_type}",
                    f"部门ID: {row.dept_id}",
                    f"创建时间: {row.create_time}",
                    f"文件路径: {row.file_path}",
                ]
            ),
            file_name=row.file_name,
            file_path=row.file_path,
            section_title="my_uploaded_file",
        )
        for row in rows
    ]
    citations = [doc.node_id for doc in documents]
    names = [row.file_name for row in rows]
    answer = "你最近上传的文件有：" + "、".join(names) if names else "当前没有查到你上传的文件。"
    return answer, documents, citations


def _query_role_department_scope(context: DBSearchContext) -> tuple[str, list[DocumentInfo], list[str]]:
    if context.role_id is None:
        return "缺少当前角色信息，无法查询角色部门范围。", [], []

    with get_sync_session() as session:
        rows = session.exec(
            select(RoleDepartmentModel, DepartmentModel, RoleModel)
            .join(DepartmentModel, DepartmentModel.dept_id == RoleDepartmentModel.dept_id)
            .join(RoleModel, RoleModel.role_id == RoleDepartmentModel.role_id)
            .where(RoleDepartmentModel.role_id == context.role_id)
        ).all()

    documents = []
    role_name = ""
    for mapping, department, role in rows:
        role_name = role.role_name
        documents.append(
            _make_doc(
                f"db://role_department/{mapping.r_d_id}",
                "\n".join(
                    [
                        f"角色ID: {role.role_id}",
                        f"角色名称: {role.role_name}",
                        f"部门ID: {department.dept_id}",
                        f"部门名称: {department.dept_name}",
                    ]
                ),
                file_name=role.role_name,
                section_title="role_department_scope",
            )
        )

    citations = [doc.node_id for doc in documents]
    dept_names = [department.dept_name for _, department, _ in rows]
    if dept_names:
        answer = f"当前角色 {role_name or context.role_id} 可访问的部门有：" + "、".join(dept_names)
    else:
        answer = "当前角色没有分配可访问的部门。"
    return answer, documents, citations


def db_search_tool(context: DBSearchContext) -> RAGResult:
    """数据库搜索工具主入口函数

    根据查询上下文推断查询类型，执行对应的数据库查询并返回格式化结果

    Args:
        context: 数据库搜索上下文对象，包含用户ID、角色ID、允许访问的部门ID等信息

    Returns:
        RAGResult: 包含查询结果、文档信息、引用等内容的标准化结果对象
    """
    # 推断查询类型并记录诊断信息
    query_kind = _infer_db_query_kind(context)
    diagnostics = [f"db_query_kind={query_kind}"]

    # 处理不支持的查询类型
    if query_kind == "unsupported":
        return _build_result(
            answer="当前结构化查询工具暂不支持这个问题类型。",
            is_sufficient=False,
            fail_reason="no_data",
            diagnostics=diagnostics + ["db_query_unsupported"],
            success=False,
        )

    try:
        # 根据查询类型分发到不同的查询处理器
        if query_kind == "accessible_departments":
            answer, documents, citations = _query_accessible_departments(context)
        elif query_kind == "accessible_file_count":
            answer, documents, citations = _query_accessible_file_count(context)
        elif query_kind == "recent_accessible_files":
            answer, documents, citations = _query_recent_accessible_files(context)
        elif query_kind == "my_uploaded_files":
            answer, documents, citations = _query_my_uploaded_files(context)
        else:
            answer, documents, citations = _query_role_department_scope(context)

        # 对查询结果进行去重处理
        documents = _dedupe_docs(documents)

        # 处理空结果情况
        if not documents:
            return _build_result(
                answer=answer,
                is_sufficient=False,
                fail_reason="no_data",
                diagnostics=diagnostics + ["db_query_no_rows"],
            )

        # 构建成功结果返回
        return _build_result(
            answer=answer,
            documents=documents,
            citations=citations,
            evidence_summary=answer,
            is_sufficient=True,
            diagnostics=diagnostics + [f"db_document_count={len(documents)}"],
        )
    except Exception as exc:
        # 处理查询过程中的异常情况
        return _build_result(
            answer="数据库查询执行失败。",
            is_sufficient=False,
            fail_reason="tool_error",
            diagnostics=diagnostics + ["db_query_exception", str(exc)],
            success=False,
        )

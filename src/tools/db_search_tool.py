from typing import Iterable

from sqlmodel import func, select

from core.custom_types import DocumentMetadata
from service.models.department import DepartmentModel
from service.models.file import FileModel
from service.models.role import RoleModel
from service.models.role_department import RoleDepartmentModel
from src.database.postgres import get_sync_session
from src.types.db_search_type import DBQueryKind, DBSearchContext
from src.types.rag_type import DocumentInfo, RAGResult


def _resolved_query_text(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip()).lower()


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _looks_like_count_query(text: str) -> bool:
    markers = [
        "多少",
        "数量",
        "几个",
        "几条",
        "总数",
        "总量",
        "count",
        "how many",
        "total",
    ]
    return _contains_any(text, markers)


def _looks_like_recent_query(text: str) -> bool:
    markers = ["最近", "最新", "recent", "latest", "刚上传", "近来"]
    return _contains_any(text, markers)


def _looks_like_file_query(text: str) -> bool:
    markers = ["文件", "文档", "资料", "上传", "file", "document", "uploaded"]
    return _contains_any(text, markers)


def _looks_like_department_query(text: str) -> bool:
    markers = ["部门", "department", "科室", "组织"]
    return _contains_any(text, markers)


def _looks_like_permission_query(text: str) -> bool:
    markers = ["权限", "可访问", "访问范围", "scope", "permission", "accessible"]
    return _contains_any(text, markers)


def _looks_like_role_query(text: str) -> bool:
    markers = ["角色", "role", "岗位"]
    return _contains_any(text, markers)


def _looks_like_first_person_query(text: str) -> bool:
    markers = ["我", "我的", "我能", "我可以", "my", "mine", "当前用户"]
    return _contains_any(text, markers)


def _infer_db_query_kind(context: DBSearchContext) -> DBQueryKind:
    text = _resolved_query_text(context.query or "", context.rewritten_query or "")

    if _looks_like_role_query(text) and (_looks_like_department_query(text) or _looks_like_permission_query(text)):
        return "role_department_scope"

    if _looks_like_department_query(text) and _looks_like_permission_query(text):
        return "accessible_departments"

    if _looks_like_first_person_query(text) and _looks_like_file_query(text):
        return "my_uploaded_files"

    if _looks_like_recent_query(text) and _looks_like_file_query(text):
        return "recent_accessible_files"

    if _looks_like_file_query(text) and _looks_like_count_query(text):
        return "accessible_file_count"

    if _looks_like_first_person_query(text) and _looks_like_department_query(text):
        return "accessible_departments"

    if _looks_like_first_person_query(text) and _looks_like_permission_query(text):
        return "accessible_departments"

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
    answer = f"当前用户可访问的文件数量是 {total}。"
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
    query_kind = _infer_db_query_kind(context)
    diagnostics = [f"db_query_kind={query_kind}"]

    if query_kind == "unsupported":
        return _build_result(
            answer="当前结构化查询工具暂不支持这个问题类型。",
            is_sufficient=False,
            fail_reason="no_data",
            diagnostics=diagnostics + ["db_query_unsupported"],
            success=False,
        )

    try:
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

        documents = _dedupe_docs(documents)

        if not documents:
            return _build_result(
                answer=answer,
                is_sufficient=False,
                fail_reason="no_data",
                diagnostics=diagnostics + ["db_query_no_rows"],
            )

        return _build_result(
            answer=answer,
            documents=documents,
            citations=citations,
            evidence_summary=answer,
            is_sufficient=True,
            diagnostics=diagnostics + [f"db_document_count={len(documents)}"],
        )
    except Exception as exc:
        return _build_result(
            answer="数据库查询执行失败。",
            is_sufficient=False,
            fail_reason="tool_error",
            diagnostics=diagnostics + ["db_query_exception", str(exc)],
            success=False,
        )

from typing import Iterable

from zhipuai import ZhipuAI

from core.custom_types import DocumentMetadata
from core.settings import settings
from src.models.llm import chatgpt_llm
from src.rag.context.builder import ContextBuilder
from src.rag.generation.generator import evaluate_evidence
from src.types.rag_type import DocumentInfo, RAGResult
from src.types.web_search_type import WebSearchContext


zhipu_client = ZhipuAI(api_key=settings.zhipuai_api_key)


def _dedupe_queries(queries: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for query in queries:
        normalized = (query or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _build_search_queries(context: WebSearchContext) -> list[str]:
    return _dedupe_queries(
        [
            context.query or "",
            context.rewritten_query or "",
            *(context.expand_query or []),
            *(context.decompose_query or []),
        ]
    )


def _normalize_search_items(raw_result) -> list:
    if raw_result is None:
        return []
    search_result = getattr(raw_result, "search_result", None)
    if search_result is None and isinstance(raw_result, dict):
        search_result = raw_result.get("search_result")

    if search_result is None:
        return []
    if isinstance(search_result, list):
        return search_result
    return [search_result]


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_node_id(link: str, fallback_index: int) -> str:
    normalized_link = _safe_text(link)
    if normalized_link:
        return normalized_link
    return f"web://result/{fallback_index}"


def _build_web_document(item, query: str, index: int) -> DocumentInfo:
    title = _safe_text(getattr(item, "title", None) if not isinstance(item, dict) else item.get("title"))
    link = _safe_text(getattr(item, "link", None) if not isinstance(item, dict) else item.get("link"))
    content = _safe_text(getattr(item, "content", None) if not isinstance(item, dict) else item.get("content"))
    media = _safe_text(getattr(item, "media", None) if not isinstance(item, dict) else item.get("media"))
    publish_date = _safe_text(
        getattr(item, "publish_date", None) if not isinstance(item, dict) else item.get("publish_date")
    )

    node_id = _normalize_node_id(link, index)
    content_text = "\n".join(
        part
        for part in [
            f"Query: {query}",
            f"Title: {title}" if title else "",
            f"Source: {media}" if media else "",
            f"Publish date: {publish_date}" if publish_date else "",
            f"Link: {link}" if link else "",
            f"Snippet: {content}" if content else "",
        ]
        if part
    )

    return DocumentInfo(
        node_id=node_id,
        content=content_text,
        metadata=DocumentMetadata(
            file_name=title or node_id,
            file_path=link,
            file_type="web",
            source="web_search",
            section_title=title,
        ),
    )


def _merge_documents(documents: list[DocumentInfo]) -> list[DocumentInfo]:
    """合并文档列表并去除重复项

    根据文档的 node_id 进行去重，保留每个 node_id 第一次出现的文档。
    主要用于合并来自不同查询的搜索结果，避免返回重复内容。

    Args:
        documents: 待合并的文档列表，包含 DocumentInfo 对象

    Returns:
        去重后的新文档列表，保持原始顺序（每个 node_id 第一次出现的顺序）
    """
    merged = []  # 存储合并后的结果
    seen = set()  # 用于记录已处理的 node_id
    for doc in documents:
        if not doc.node_id or doc.node_id in seen:
            continue  # 跳过无 node_id 或已处理的文档
        seen.add(doc.node_id)
        merged.append(doc)
    return merged


def _looks_self_declared_insufficient(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if not normalized:
        return True
    markers = [
        "insufficient evidence",
        "not enough evidence",
        "unable to answer",
        "cannot answer",
        "no relevant evidence",
        "缺乏",
        "不足",
        "无法回答",
        "无法稳定回答",
        "没有足够",
        "未检索到",
    ]
    return any(marker in normalized for marker in markers)


def _normalize_citations(raw_citations, allowed_citations: list[str]) -> list[str]:
    allowed_set = {item for item in allowed_citations if item}
    normalized = []
    seen = set()

    for item in raw_citations or []:
        citation = str(item).strip()
        if not citation:
            continue
        lowered = citation.lower()
        if lowered.startswith("node_id") and citation not in allowed_set:
            continue
        if citation not in allowed_set:
            continue
        if citation in seen:
            continue
        seen.add(citation)
        normalized.append(citation)

    return normalized


def _build_result(
    *,
    answer: str,
    documents: list[DocumentInfo] | None = None,
    citations: list[str] | None = None,
    evidence_summary: str | None = None,
    is_sufficient: bool,
    fail_reason=None,
    retrieval_queries: list[str] | None = None,
    retrieval_candidate_node_ids: list[str] | None = None,
    diagnostics: list[str] | None = None,
    success: bool = True,
) -> RAGResult:
    """构建 RAG 结果对象

    用于封装 Web 搜索工具的执行结果，统一返回 RAGResult 格式的数据结构。
    所有可选参数都提供了默认值，确保返回的对象具有完整的结构。

    Args:
        answer: 生成的最终回答文本
        documents: 检索到的文档列表，默认为空列表
        citations: 引用的文档节点ID列表，默认为空列表
        evidence_summary: 证据摘要文本，未提供时使用answer作为默认值
        is_sufficient: 布尔值，表示证据是否充分
        fail_reason: 失败原因标识字符串，可选
        retrieval_queries: 实际使用的检索查询列表，默认为空列表
        retrieval_candidate_node_ids: 候选检索节点ID列表，默认为空列表
        diagnostics: 诊断信息列表，用于调试和日志记录，默认为空列表
        success: 操作是否成功，默认为True

    Returns:
        构建好的 RAGResult 对象，包含所有Web搜索相关的返回信息
    """
    return RAGResult(
        success=success,
        name="web_search",
        answer=answer,
        evidence_summary=evidence_summary if evidence_summary is not None else answer,
        documents=documents or [],
        citations=citations or [],
        is_sufficient=is_sufficient,
        fail_reason=fail_reason,
        retrieval_queries=retrieval_queries or [],
        retrieval_candidate_node_ids=retrieval_candidate_node_ids or [],
        rerank_node_ids=retrieval_candidate_node_ids or [],  # 复用候选节点ID作为重排节点ID
        diagnostics=diagnostics or [],
    )


def _evaluate_web_evidence(query: str, documents: list[DocumentInfo]):
    """评估 Web 搜索结果的证据充分性

    使用上下文构建器和 LLM 模型对搜索结果进行评估，判断证据是否充分，
    并生成相关的引用、诊断信息和评估结果。

    Args:
        query: 原始搜索查询字符串
        documents: 检索到的文档信息列表，包含 DocumentInfo 对象

    Returns:
        返回一个元组，包含:
        - response: 评估响应对象
        - citations: 引用节点ID列表
        - is_sufficient: 布尔值，表示证据是否充分
        - fail_reason: 失败原因标识字符串
        - diagnostics: 诊断信息列表
    """
    # 构建搜索结果的上下文
    context_builder = ContextBuilder()
    context = context_builder.run([doc.model_dump() for doc in documents])

    # 使用 LLM 评估证据质量
    response = evaluate_evidence(chatgpt_llm, query, context)

    # 处理引用信息：仅接受真实引用ID，若模型输出占位符则回退到文档node_id
    available_citations = [doc.node_id for doc in documents if doc.node_id]
    citations = _normalize_citations(response.citations, available_citations)
    if not citations:
        citations = available_citations

    # 初始化评估结果和诊断信息
    is_sufficient = bool(response.is_sufficient)
    fail_reason = response.fail_reason
    diagnostics = []

    # 检查文档是否为空
    if not documents:
        is_sufficient = False
        fail_reason = fail_reason or "no_data"
        diagnostics.append("web_evidence_no_documents")

    # 检查证据摘要是否为空
    if not (response.evidence_summary or "").strip():
        is_sufficient = False
        fail_reason = fail_reason or "insufficient_context"
        diagnostics.append("web_evidence_empty_summary")

    # 检查引用是否为空
    if not citations:
        is_sufficient = False
        fail_reason = fail_reason or "insufficient_context"
        diagnostics.append("web_evidence_missing_citations")

    # 检查模型是否自述证据不足
    if _looks_self_declared_insufficient(response.evidence_summary or ""):
        is_sufficient = False
        fail_reason = fail_reason or "insufficient_context"
        diagnostics.append("web_evidence_self_declared_insufficient")

    return response, citations, is_sufficient, fail_reason, diagnostics


def web_search_tool(web_search_context: WebSearchContext) -> RAGResult:
    """执行 Web 搜索并返回 RAG 格式的结果

    该工具函数负责处理 Web 搜索的整个流程，包括：
    1. 构建搜索查询
    2. 执行搜索并收集结果
    3. 评估搜索结果的质量
    4. 返回标准化格式的结果

    Args:
        web_search_context: Web 搜索上下文对象，包含查询、搜索引擎等配置信息

    Returns:
        返回 RAGResult 对象，包含搜索结果、评估信息、诊断日志等
    """
    # 构建搜索查询列表（去重后的）
    search_queries = _build_search_queries(web_search_context)
    if not search_queries:
        return _build_result(
            answer="暂无可执行的 Web 搜索查询。",
            is_sufficient=False,
            fail_reason="no_data",
            retrieval_queries=[],
            diagnostics=["web_search_empty_queries"],
            success=False,
        )

    try:
        collected_documents: list[DocumentInfo] = []
        # 初始化诊断信息，记录使用的搜索引擎
        diagnostics = [f"web_search_engine={web_search_context.search_engine}"]
        # 计算实际搜索数量，限制在1-10之间
        count = max(1, min(int(web_search_context.count or web_search_context.retrieval_top_k or 5), 10))

        # 遍历每个查询执行搜索
        for query in search_queries:
            # 调用智谱AI的Web搜索API
            raw_result = zhipu_client.web_search.web_search(
                search_engine=web_search_context.search_engine,
                search_query=query,
                count=count,
                content_size="high",
            )
            # 规范化搜索结果
            items = _normalize_search_items(raw_result)
            diagnostics.append(f"web_search_results:{query}:{len(items)}")
            # 将每个搜索结果转换为标准文档格式
            for index, item in enumerate(items, start=1):
                collected_documents.append(_build_web_document(item, query, index))

        # 合并文档并去重
        documents = _merge_documents(collected_documents)
        # 提取所有文档的node_id作为候选节点
        retrieval_candidate_node_ids = [doc.node_id for doc in documents if doc.node_id]

        # 检查是否获取到有效文档
        if not documents:
            return _build_result(
                answer="Web 搜索未返回可用证据。",
                is_sufficient=False,
                fail_reason="no_data",
                retrieval_queries=search_queries,
                retrieval_candidate_node_ids=[],
                diagnostics=diagnostics + ["web_search_no_results"],
            )

        # 确定用于评估的主要查询文本
        query_text = web_search_context.rewritten_query or web_search_context.query or search_queries[0]
        # 评估搜索结果的质量和充分性
        response, citations, is_sufficient, fail_reason, evidence_diagnostics = _evaluate_web_evidence(
            query_text,
            documents,
        )

        # 构建最终结果对象
        return _build_result(
            answer=response.evidence_summary or "",
            documents=documents,
            citations=citations,
            evidence_summary=response.evidence_summary or "",
            is_sufficient=is_sufficient,
            fail_reason=fail_reason,
            retrieval_queries=search_queries,
            retrieval_candidate_node_ids=retrieval_candidate_node_ids,
            diagnostics=diagnostics + evidence_diagnostics + ["web_search_completed"],
        )
    except Exception as exc:
        # 异常处理：返回错误结果
        return _build_result(
            answer="Web 搜索执行失败。",
            is_sufficient=False,
            fail_reason="tool_error",
            retrieval_queries=search_queries,
            diagnostics=["web_search_exception", str(exc)],
            success=False,
        )




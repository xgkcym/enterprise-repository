from __future__ import annotations

import argparse
import json
from typing import Any
from uuid import uuid4

from core.settings import settings
from src.agent.graph import graph
from src.types.agent_state import State


def _build_citation_label(document: Any) -> str:
    metadata = getattr(document, "metadata", None)
    if metadata is None and isinstance(document, dict):
        metadata = document.get("metadata") or {}

    def pick(name: str, default=None):
        if metadata is None:
            return default
        if isinstance(metadata, dict):
            return metadata.get(name, default)
        return getattr(metadata, name, default)

    file_name = pick("file_name", "") or "未知文档"
    page = pick("page", None)
    sheet_name = pick("sheet_name", "") or ""
    # section_title = pick("section_title", "") or ""
    # chunk_index = pick("chunk_index", None)

    extras = []
    if page not in (None, "", 0):
        extras.append(f"第{page}页")
    if sheet_name:
        extras.append(f"Sheet:{sheet_name}")
    # if section_title:
    #     extras.append(section_title)
    # if chunk_index not in (None, "", 0):
    #     extras.append(f"片段{chunk_index}")

    if extras:
        return f"{file_name} ({' | '.join(str(item) for item in extras)})"
    return file_name


def _build_citation_details(last_rag_result: Any) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """从RAG结果中构建引用详情信息

    处理RAG结果中的引用信息，生成三种形式的引用数据：
    1. 原始引用ID列表
    2. 可读的引用标签列表
    3. 详细的引用元数据字典列表

    Args:
        last_rag_result: RAG处理结果对象，应包含citations和documents属性

    Returns:
        tuple: 包含三个元素的元组：
            - raw_citations: 原始引用ID列表
            - citation_labels: 可读的引用标签列表
            - citation_details: 包含详细元数据的引用字典列表
    """
    # 获取原始引用列表和文档列表，确保返回的是列表类型
    raw_citations = list(getattr(last_rag_result, "citations", []) or [])
    documents = list(getattr(last_rag_result, "documents", []) or [])

    # 构建文档映射表，以node_id为键
    doc_map: dict[str, Any] = {}
    for doc in documents:
        node_id = getattr(doc, "node_id", None)
        if node_id and node_id not in doc_map:
            doc_map[node_id] = doc

    # 初始化返回结果容器
    citation_labels: list[str] = []
    citation_details: list[dict[str, Any]] = []

    # 处理每个引用，生成标签和详情信息
    for citation in raw_citations:
        # 获取对应的文档对象
        doc = doc_map.get(citation)
        # 生成可读的引用标签
        label = _build_citation_label(doc) if doc else str(citation)
        citation_labels.append(label)

        # 构建基础详情信息
        detail = {
            "node_id": citation,
            "label": label,
        }

        # 如果文档存在，添加元数据信息
        if doc:
            metadata = getattr(doc, "metadata", None)
            if hasattr(metadata, "model_dump"):  # 处理Pydantic模型
                detail["metadata"] = metadata.model_dump()
            elif isinstance(metadata, dict):  # 处理普通字典
                detail["metadata"] = metadata
        citation_details.append(detail)

    return raw_citations, citation_labels, citation_details


def run_agent(
    query: str,
    *,
    user_id: str = "",
    session_id: str = "",
    user_profile: dict[str, Any] | None = None,
    chat_history: list[str] | None = None,
    max_steps: int = 20,
    output_level: str | None = None,
) -> State:
    """Run the agent graph and return the final state."""
    initial_state = State(
        query=query,
        run_id=str(uuid4()),
        user_id=user_id,
        session_id=session_id,
        user_profile=user_profile,
        chat_history=chat_history or [],
        max_steps=max_steps,
        output_level=output_level or settings.agent_output_level,
    )
    result = graph.invoke(initial_state)
    if isinstance(result, State):
        return result
    return State(**result)


def summarize_trace(state: State) -> list[dict[str, Any]]:
    """Convert trace records into a JSON-friendly list."""
    rows = []
    for item in state.trace:
        rows.append(
            {
                "step": item.step,
                "event": item.event_name,
                "kind": item.event_kind,
                "status": item.status,
                "attempt": item.attempt,
                "duration_ms": item.duration_ms,
                "fail_reason": item.fail_reason,
                "message": item.message,
                "diagnostics": item.diagnostics,
            }
        )
    return rows


def build_run_report(state: State) -> dict[str, Any]:
    last_rag_result = state.last_rag_result
    raw_citations, citation_labels, citation_details = _build_citation_details(last_rag_result) if last_rag_result else ([], [], [])
    sub_query_results = []
    for item in state.sub_query_results:
        if hasattr(item, "model_dump"):
            sub_query_results.append(item.model_dump())
        elif isinstance(item, dict):
            sub_query_results.append(item)

    return {
        "run_id": state.run_id,
        "query": state.query,
        "resolved_query": state.resolved_query,
        "status": state.status,
        "output_level": state.output_level,
        "action": state.action,
        "answer": state.answer,
        "citations": citation_labels,
        "raw_citations": raw_citations,
        "citation_details": citation_details,
        "reason": state.reason,
        "fail_reason": state.fail_reason,
        "current_step": state.current_step,
        "max_steps": state.max_steps,
        "working_memory": state.working_memory,
        "short_term_memory": state.short_term_memory,
        "diagnostics": state.diagnostics,
        "rewrite_query": state.rewrite_query,
        "expand_query": state.expand_query,
        "decompose_query": state.decompose_query,
        "sub_query_results": sub_query_results,
        "last_rag_result": {
            "answer": getattr(last_rag_result, "answer", ""),
            "evidence_summary": getattr(last_rag_result, "evidence_summary", ""),
            "is_sufficient": getattr(last_rag_result, "is_sufficient", False),
            "fail_reason": getattr(last_rag_result, "fail_reason", None),
            "confidence": getattr(last_rag_result, "confidence", None),
            "citations": citation_labels,
            "raw_citations": raw_citations,
            "citation_details": citation_details,
            "retrieval_queries": getattr(last_rag_result, "retrieval_queries", []),
            "retrieval_candidate_node_ids": getattr(last_rag_result, "retrieval_candidate_node_ids", []),
            "rerank_node_ids": getattr(last_rag_result, "rerank_node_ids", []),
            "diagnostics": getattr(last_rag_result, "diagnostics", []),
            "document_count": len(getattr(last_rag_result, "documents", []) or []),
        }
        if last_rag_result
        else None,
        "trace": summarize_trace(state),
    }


def print_run_report(state: State) -> None:
    print(json.dumps(build_run_report(state), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Run the Agentic RAG graph for local validation.")
    # parser.add_argument(
    #     "query",
    #     default="根据多个会议记录，不同部门对新能源行业景气度的看法有哪些共同点和差异？",
    #     help="User query",
    # )
    # parser.add_argument("--user-id", default="", help="User ID")
    # parser.add_argument("--session-id", default="", help="Session ID")
    # parser.add_argument("--max-steps", type=int, default=6, help="Maximum agent steps")
    # args = parser.parse_args()

    final_state = run_agent(
        query="python怎么学？",
        # user_id=args.user_id,
        # session_id=args.session_id,
        # max_steps=args.max_steps,
    )
    print_run_report(final_state)

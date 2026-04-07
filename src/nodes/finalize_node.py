import time

from langchain_core.messages import HumanMessage

from src.config.llm_config import LLMService
from src.models.llm import chatgpt_llm
from src.nodes.helpers import build_state_patch, create_event, finalize_event
from src.prompts.agent.finalize_prompt import FINALIZE_PROMPT
from src.types.agent_state import State
from src.types.event_type import ReasoningEvent
from src.types.final_answer_type import FinalAnswerResult


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


def _build_sub_query_context(state: State) -> str:
    if not state.sub_query_results:
        return "No sub-query evidence."

    blocks = []
    for index, item in enumerate(state.sub_query_results, start=1):
        summary = getattr(item, "evidence_summary", "") or getattr(item, "answer", "")
        blocks.append(
            "\n".join(
                [
                    f"[Sub-query {index}]",
                    f"Question: {item.sub_query}",
                    f"Evidence summary: {summary}",
                    f"Is sufficient: {item.is_sufficient}",
                    f"Fail reason: {item.fail_reason or ''}",
                ]
            )
        )
    return "\n\n".join(blocks)


def _build_fallback_final_answer(state: State) -> FinalAnswerResult:
    last_rag_result = state.last_rag_result
    evidence_summary = ""
    citations = []
    fail_reason = state.fail_reason
    is_sufficient = False

    if last_rag_result:
        evidence_summary = last_rag_result.evidence_summary or last_rag_result.answer or ""
        citations = list(last_rag_result.citations or [])
        fail_reason = last_rag_result.fail_reason or fail_reason
        is_sufficient = bool(last_rag_result.is_sufficient)

    if evidence_summary:
        answer = evidence_summary
    elif fail_reason == "no_data":
        answer = "当前知识库中未检索到足够相关内容，暂时无法给出可靠答案。"
    else:
        answer = "当前证据不足，暂时无法稳定回答该问题。"

    return FinalAnswerResult(
        success=bool(answer) and is_sufficient,
        answer=answer,
        citations=citations,
        reason="finalize_fallback",
        fail_reason=fail_reason,
        diagnostics=["finalize_fallback_used"],
    )


def finalize_node(state: State):
    """最终答案生成节点

    根据RAG结果和子查询证据生成最终答案，处理失败情况并返回状态补丁

    Args:
        state: 当前代理状态对象，包含查询、RAG结果等信息

    Returns:
        包含最终答案和状态更新的补丁对象
    """
    # 记录开始时间用于事件追踪
    start_time = time.time()

    # 创建推理事件用于记录处理过程
    event = create_event(
        ReasoningEvent,
        name="finalize",
        input_data={
            "query": state.query,
            "evidence_summary": getattr(state.last_rag_result, "evidence_summary", ""),
        },
        max_attempt=1,  # 最多尝试1次
    )
    event.attempt = 1  # 设置当前尝试次数

    # 从状态中提取最后一次RAG结果
    last_rag_result = state.last_rag_result
    evidence_summary = ""
    citations = []
    fail_reason = state.fail_reason
    is_sufficient = False

    # 如果有RAG结果，提取相关信息
    if last_rag_result:
        evidence_summary = last_rag_result.evidence_summary or last_rag_result.answer or ""
        citations = list(last_rag_result.citations or [])
        fail_reason = last_rag_result.fail_reason or fail_reason
        is_sufficient = bool(last_rag_result.is_sufficient)

    # 构建最终答案生成的提示词模板
    prompt = FINALIZE_PROMPT.format(
        query=state.query or "",
        evidence_summary=evidence_summary or "No evidence summary available.",
        sub_query_context=_build_sub_query_context(state),  # 构建子查询上下文
        available_citations=", ".join(citations) if citations else "None",
    )

    try:
        # 调用LLM服务生成最终答案
        result: FinalAnswerResult = LLMService.invoke(
            llm=chatgpt_llm,
            messages=[HumanMessage(content=prompt)],
            schema=FinalAnswerResult,
        )

        # 后处理LLM返回的结果
        result.citations = _normalize_citations(result.citations, citations)  # 规范化引用
        if not result.citations:
            result.citations = citations  # 如果没有新引用则保留原始引用
        if result.fail_reason is None:
            result.fail_reason = fail_reason  # 保留原始失败原因
        result.success = bool(result.answer) and is_sufficient  # 判断是否成功
        if not result.reason:
            # 设置默认原因
            result.reason = "finalize_completed" if result.success else "finalize_constrained"
        if not result.diagnostics:
            result.diagnostics = ["finalize_llm_completed"]  # 设置默认诊断信息
    except Exception:
        # LLM调用失败时使用后备方案生成答案
        result = _build_fallback_final_answer(state)

    # 完成事件记录
    event = finalize_event(event, result, start_time)

    # 构建并返回状态补丁
    return build_state_patch(
        state,
        event,
        action="finish",  # 标记为完成动作
        answer=result.answer,  # 最终答案
        citations=result.citations,  # 引用列表
        reason=result.reason or "",  # 处理原因
        status="success" if result.success else "failed",  # 成功/失败状态
        fail_reason=result.fail_reason,  # 失败原因(如果有)
    )

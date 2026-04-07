import time

from langchain_core.messages import HumanMessage

from src.config.llm_config import LLMService
from src.models.llm import chatgpt_llm
from src.nodes.helpers import build_state_patch, create_event, finalize_event
from src.prompts.agent.direct_answer_prompt import DIRECT_ANSWER_PROMPT
from src.prompts.agent.finalize_prompt import FINALIZE_PROMPT
from src.types.agent_state import State
from src.types.event_type import ReasoningEvent
from src.types.final_answer_type import FinalAnswerResult


def _normalize_citations(raw_citations, allowed_citations: list[str]) -> list[str]:
    """规范化引用列表，确保引用符合要求且不重复

    参数:
        raw_citations: 原始引用列表，可能包含None或无效值
        allowed_citations: 允许的引用列表，作为白名单检查

    返回:
        list[str]: 规范化后的引用列表，满足以下条件：
            1. 非空且已去除两端空格
            2. 存在于允许的引用列表中
            3. 不包含重复项
            4. 忽略以"node_id"开头但不在白名单中的引用
    """
    # 创建允许的引用集合，过滤掉空值
    allowed_set = {item for item in allowed_citations if item}
    normalized = []  # 存储规范化后的结果
    seen = set()  # 用于去重检查

    # 遍历原始引用列表（处理None情况）
    for item in raw_citations or []:
        # 转换为字符串并去除两端空格
        citation = str(item).strip()
        if not citation:  # 跳过空字符串
            continue

        lowered = citation.lower()
        # 特殊处理以"node_id"开头的引用：必须严格匹配白名单
        if lowered.startswith("node_id") and citation not in allowed_set:
            continue

        # 检查引用是否在白名单中
        if citation not in allowed_set:
            continue

        # 检查是否已存在（去重）
        if citation in seen:
            continue

        # 添加到结果集
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


def _build_fallback_final_answer(state: State, *, direct_answer_mode: bool = False) -> FinalAnswerResult:
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
    elif direct_answer_mode:
        answer = "这个问题不依赖知识库检索，我可以直接回答；如果你希望，我也可以继续展开说明。"
    elif fail_reason == "no_data":
        answer = "当前知识库中未检索到足够相关内容，暂时无法给出可靠答案。"
    else:
        answer = "当前证据不足，暂时无法稳定回答该问题。"

    return FinalAnswerResult(
        success=bool(answer) and (is_sufficient or direct_answer_mode),
        answer=answer,
        citations=[] if direct_answer_mode else citations,
        reason="direct_answer_fallback" if direct_answer_mode else "finalize_fallback",
        fail_reason=None if direct_answer_mode else fail_reason,
        diagnostics=["direct_answer_fallback_used"] if direct_answer_mode else ["finalize_fallback_used"],
    )


def _build_direct_answer_prompt(state: State) -> str:
    chat_history = "\n".join(state.chat_history[-8:]) if state.chat_history else "None"
    effective_query = state.working_query or state.resolved_query or state.query or ""
    return DIRECT_ANSWER_PROMPT.format(
        raw_query=state.query or "",
        query=effective_query,
        chat_history=chat_history,
        output_level=state.output_level,
    ).strip()


def finalize_node(state: State):
    """最终答案生成节点，负责整合所有信息生成最终回答

    参数:
        state: 当前状态对象，包含查询、检索结果等信息

    返回:
        更新后的状态补丁，包含最终答案、引用、状态等信息
    """
    effective_query = state.working_query or state.resolved_query or state.query or ""

    # 记录开始时间用于性能监控
    start_time = time.time()

    # 创建推理事件用于追踪处理过程
    event = create_event(
        ReasoningEvent,
        name="finalize",
        input_data={
            "query": effective_query,
            "evidence_summary": getattr(state.last_rag_result, "evidence_summary", ""),
        },
        max_attempt=1,
    )
    event.attempt = 1  # 设置尝试次数

    # 从状态中提取关键信息
    last_rag_result = state.last_rag_result
    evidence_summary = ""
    citations = []
    fail_reason = state.fail_reason
    is_sufficient = False

    # 如果有最后一次RAG结果，提取相关信息
    if last_rag_result:
        evidence_summary = last_rag_result.evidence_summary or last_rag_result.answer or ""
        citations = list(last_rag_result.citations or [])
        fail_reason = last_rag_result.fail_reason or fail_reason
        is_sufficient = bool(last_rag_result.is_sufficient)

    # 判断是否启用直接回答模式（无证据且无子查询结果）
    direct_answer_mode = not evidence_summary and not state.sub_query_results

    # 根据模式构建不同的提示词
    if direct_answer_mode:
        prompt = _build_direct_answer_prompt(state)
    else:
        prompt = FINALIZE_PROMPT.format(
            raw_query=state.query or "",
            query=effective_query,
            evidence_summary=evidence_summary or "No evidence summary available.",
            sub_query_context=_build_sub_query_context(state),
            available_citations=", ".join(citations) if citations else "None",
            output_level=state.output_level,
        )

    try:
        # 调用LLM服务生成最终答案
        result: FinalAnswerResult = LLMService.invoke(
            llm=chatgpt_llm,
            messages=[HumanMessage(content=prompt)],
            schema=FinalAnswerResult,
        )

        # 对结果进行后处理
        result.citations = [] if direct_answer_mode else _normalize_citations(result.citations, citations)
        if not result.citations and not direct_answer_mode:
            result.citations = citations  # 回退到原始引用列表
        if result.fail_reason is None:
            result.fail_reason = None if direct_answer_mode else fail_reason
        result.success = bool(result.answer) and (is_sufficient or direct_answer_mode)

        # 设置默认原因字段
        if not result.reason:
            result.reason = (
                "direct_answer_completed"
                if direct_answer_mode and result.success
                else "finalize_completed"
                if result.success
                else "finalize_constrained"
            )

        # 设置默认诊断信息
        if not result.diagnostics:
            result.diagnostics = ["finalize_llm_completed"]
        if direct_answer_mode:
            result.citations = []
            result.fail_reason = None
            result.diagnostics.append("finalize:direct_answer_mode")
    except Exception:
        # 异常处理：生成回退答案
        result = _build_fallback_final_answer(state, direct_answer_mode=direct_answer_mode)

    # 完成事件记录
    event = finalize_event(event, result, start_time)

    # 构建并返回状态补丁
    return build_state_patch(
        state,
        event,
        action="finish",
        answer=result.answer,
        citations=result.citations,
        reason=result.reason or "",
        status="success" if result.success else "failed",
        fail_reason=result.fail_reason,
    )

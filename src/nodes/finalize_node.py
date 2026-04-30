import time

from langchain_core.messages import HumanMessage

from src.agent.answer_stream import get_answer_token_handler
from src.agent.profile_utils import extract_preferred_topics
from src.config.llm_config import LLMService
from src.models.llm import chatgpt_llm
from src.nodes.helpers import build_state_patch, create_event, finalize_event
from src.prompts.agent.finalize_prompt import FINALIZE_PROMPT, FINALIZE_STREAM_PROMPT
from src.types.agent_state import State
from src.types.event_type import ReasoningEvent
from src.types.final_answer_type import FinalAnswerResult


def _prefers_citations(state: State) -> bool:
    profile = state.user_profile or {}
    return bool(profile.get("prefers_citations", True))


def _preferred_language(state: State) -> str:
    profile = state.user_profile or {}
    return str(profile.get("preferred_language") or "zh-CN").strip() or "zh-CN"


def _preferred_topics(state: State) -> list[str]:
    return extract_preferred_topics(state.user_profile or {})


def _normalize_citations(raw_citations, allowed_citations: list[str]) -> list[str]:
    allowed_set = {item for item in allowed_citations if item}
    normalized: list[str] = []
    seen: set[str] = set()

    for item in raw_citations or []:
        citation = str(item).strip()
        if not citation:
            continue
        if citation not in allowed_set or citation in seen:
            continue
        seen.add(citation)
        normalized.append(citation)

    return normalized


def _build_sub_query_context(state: State) -> str:
    if not state.sub_query_results:
        return "无子查询证据。"

    blocks = []
    for index, item in enumerate(state.sub_query_results, start=1):
        summary = getattr(item, "evidence_summary", "") or getattr(item, "answer", "")
        blocks.append(
            "\n".join(
                [
                    f"[子查询 {index}]",
                    f"问题：{item.sub_query}",
                    f"证据摘要：{summary}",
                    f"证据是否充分：{item.is_sufficient}",
                    f"失败原因：{item.fail_reason or ''}",
                ]
            )
        )
    return "\n\n".join(blocks)


def _append_long_term_memory_hint(state: State, prompt: str, *, stream_mode: bool) -> str:
    context = (state.long_term_memory_context or "").strip()
    if not context:
        return prompt

    instructions = (
        "长时记忆可用于用户语言、风格偏好以及其他已保存的个人偏好。\n"
        "如果当前证据已经支持答案，不要让长时记忆改变、扩展或覆盖基于证据的结论。\n"
        "仅当用户明确询问自己的已保存画像、偏好、身份或历史，且答案无法由检索证据支撑时，才直接使用长时记忆内容。\n"
        "不要将长时记忆当作企业事实、检索证据、已上传文件、外部事实或实时信息的文档证据。\n"
        "如果长时记忆与当前证据冲突，信任当前证据。\n"
        "如果长时记忆与当前对话上下文冲突，信任当前对话上下文。\n"
        "不要提及隐藏的记忆系统。\n"
    )
    section_title = "[长时记忆提示]" if stream_mode else "[长时记忆上下文]"
    return f"{prompt}\n\n{section_title}\n{context}\n\n{instructions}"


def _build_finalize_prompt(
    state: State,
    *,
    effective_query: str,
    evidence_summary: str,
    citations: list[str],
) -> str:
    prompt = FINALIZE_PROMPT.format(
        raw_query=state.query or "",
        query=effective_query,
        evidence_summary=evidence_summary or "无可用证据摘要。",
        sub_query_context=_build_sub_query_context(state),
        available_citations=", ".join(citations) if citations else "无",
        output_level=state.output_level,
        preferred_language=_preferred_language(state),
        prefers_citations="是" if _prefers_citations(state) else "否",
        preferred_topics=", ".join(_preferred_topics(state)) or "无",
    )
    return _append_long_term_memory_hint(state, prompt, stream_mode=False)


def _build_finalize_stream_prompt(
    state: State,
    *,
    effective_query: str,
    evidence_summary: str,
) -> str:
    prompt = FINALIZE_STREAM_PROMPT.format(
        raw_query=state.query or "",
        query=effective_query,
        evidence_summary=evidence_summary or "无可用证据摘要。",
        sub_query_context=_build_sub_query_context(state),
        output_level=state.output_level,
        preferred_language=_preferred_language(state),
        preferred_topics=", ".join(_preferred_topics(state)) or "无",
    ).strip()
    return _append_long_term_memory_hint(state, prompt, stream_mode=True)


def _build_fallback_final_answer(state: State) -> FinalAnswerResult:
    last_rag_result = state.last_rag_result
    evidence_summary = ""
    citations: list[str] = []
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
        answer = "未能为这个问题检索到可靠的财报证据。"
    else:
        answer = "当前证据不足，无法生成可靠答案。"

    return FinalAnswerResult(
        success=bool(answer) and is_sufficient,
        answer=answer,
        citations=citations if _prefers_citations(state) else [],
        reason="finalize_fallback",
        fail_reason=fail_reason,
        diagnostics=["finalize_fallback_used"],
    )


def _invoke_finalize_result(
    state: State,
    *,
    effective_query: str,
    evidence_summary: str,
    citations: list[str],
    fail_reason: str | None,
    is_sufficient: bool,
) -> FinalAnswerResult:
    result: FinalAnswerResult = LLMService.invoke(
        llm=chatgpt_llm,
        messages=[
            HumanMessage(
                content=_build_finalize_prompt(
                    state,
                    effective_query=effective_query,
                    evidence_summary=evidence_summary,
                    citations=citations,
                )
            )
        ],
        schema=FinalAnswerResult,
    )
    result.citations = _normalize_citations(result.citations, citations)
    if not result.citations:
        result.citations = citations
    if result.fail_reason is None:
        result.fail_reason = fail_reason
    result.success = bool((result.answer or "").strip()) and is_sufficient
    if not result.reason:
        result.reason = "finalize_completed" if result.success else "finalize_constrained"
    if not result.diagnostics:
        result.diagnostics = ["finalize_llm_completed"]
    if state.long_term_memory_used:
        result.diagnostics.append("long_term_memory_hint_applied:finalize")
    if not _prefers_citations(state):
        result.citations = []
    return result


def _stream_finalize_result(
    state: State,
    *,
    effective_query: str,
    evidence_summary: str,
    citations: list[str],
    fail_reason: str | None,
    is_sufficient: bool,
) -> FinalAnswerResult:
    handler = get_answer_token_handler()
    if handler is None:
        raise RuntimeError("回答 token 处理器未绑定")

    def on_token(token: str) -> None:
        handler(token)

    answer = LLMService.stream_text(
        llm=chatgpt_llm,
        messages=[
            HumanMessage(
                content=_build_finalize_stream_prompt(
                    state,
                    effective_query=effective_query,
                    evidence_summary=evidence_summary,
                )
            )
        ],
        on_token=on_token,
    ).strip()

    diagnostics = ["finalize_llm_stream_completed"]
    if state.long_term_memory_used:
        diagnostics.append("long_term_memory_hint_applied:finalize")

    return FinalAnswerResult(
        success=bool(answer) and is_sufficient,
        answer=answer,
        citations=citations if _prefers_citations(state) else [],
        reason="finalize_completed" if answer and is_sufficient else "finalize_constrained",
        fail_reason=fail_reason,
        diagnostics=diagnostics,
    )


def finalize_node(state: State):
    effective_query = state.working_query or state.resolved_query or state.query or ""
    start_time = time.time()

    event = create_event(
        ReasoningEvent,
        name="finalize",
        input_data={
            "query": effective_query,
            "evidence_summary": getattr(state.last_rag_result, "evidence_summary", ""),
        },
        max_attempt=1,
    )
    event.attempt = 1

    last_rag_result = state.last_rag_result
    evidence_summary = ""
    citations: list[str] = []
    fail_reason = state.fail_reason
    is_sufficient = False

    if last_rag_result:
        evidence_summary = last_rag_result.evidence_summary or last_rag_result.answer or ""
        citations = list(last_rag_result.citations or [])
        fail_reason = last_rag_result.fail_reason or fail_reason
        is_sufficient = bool(last_rag_result.is_sufficient)

    try:
        if get_answer_token_handler() is not None:
            try:
                result = _stream_finalize_result(
                    state,
                    effective_query=effective_query,
                    evidence_summary=evidence_summary,
                    citations=citations,
                    fail_reason=fail_reason,
                    is_sufficient=is_sufficient,
                )
            except Exception:
                result = _invoke_finalize_result(
                    state,
                    effective_query=effective_query,
                    evidence_summary=evidence_summary,
                    citations=citations,
                    fail_reason=fail_reason,
                    is_sufficient=is_sufficient,
                )
                result.diagnostics.append("finalize_stream_fallback_to_structured")
        else:
            result = _invoke_finalize_result(
                state,
                effective_query=effective_query,
                evidence_summary=evidence_summary,
                citations=citations,
                fail_reason=fail_reason,
                is_sufficient=is_sufficient,
            )
    except Exception:
        result = _build_fallback_final_answer(state)

    if not _prefers_citations(state):
        result.citations = []

    event = finalize_event(event, result, start_time)

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

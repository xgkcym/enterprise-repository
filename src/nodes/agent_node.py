from src.agent.policy import (
    _looks_like_external_query,
    _looks_like_structured_db_query,
    decide_initial_action,
    get_allowed_actions,
    guard_input,
    is_web_search_allowed,
    should_decompose_query,
    should_force_finish,
    should_rewrite_query,
)
from src.types.agent_state import State


DISALLOWED_INPUT_REASONS = {
    "illegal_cyber_activity",
    "privacy_exfiltration",
    "illegal_deception_request",
}


def _has_finalize_material(state: State) -> bool:
    last_rag_result = state.last_rag_result
    if last_rag_result:
        if last_rag_result.documents:
            return True
        if last_rag_result.evidence_summary or last_rag_result.answer:
            return True
    return bool(state.sub_query_results)


def _can_finalize(state: State, *, allow_partial: bool = False) -> bool:
    last_rag_result = state.last_rag_result
    if not last_rag_result:
        return False

    has_summary = bool((last_rag_result.evidence_summary or last_rag_result.answer or "").strip())
    has_citations = bool(last_rag_result.citations)
    has_documents = bool(last_rag_result.documents)
    is_sufficient = bool(last_rag_result.is_sufficient)
    fail_reason = getattr(last_rag_result, "fail_reason", None)

    if is_sufficient and has_summary and has_citations and has_documents:
        return True

    if not allow_partial:
        return False

    return has_summary and (has_citations or has_documents) and fail_reason in {
        "insufficient_context",
        "ambiguous_query",
    }


def _build_finish_response(
    state: State,
    *,
    answer: str,
    reason: str = "",
    status: str = "success",
    fail_reason=None,
    diagnostics=None,
):
    return {
        "action": "finish",
        "answer": answer,
        "reason": reason,
        "status": status,
        "fail_reason": fail_reason,
        "diagnostics": diagnostics or state.diagnostics,
    }


def _has_event(state: State, name: str) -> bool:
    return any(item.name == name for item in state.action_history)


def _reasoning_attempts(state: State) -> int:
    return sum(
        1
        for item in state.action_history
        if item.kind == "reasoning" and item.name in {"rewrite_query", "expand_query", "decompose_query"}
    )


def _select_tool_after_reasoning(state: State, query: str) -> tuple[str, str]:
    if _looks_like_structured_db_query(query):
        return "db_search", "reasoning_completed_route_to_db_search"
    if is_web_search_allowed(state) and _looks_like_external_query(query):
        return "web_search", "reasoning_completed_route_to_web_search"
    return "rag", "reasoning_completed_route_to_rag"


def _select_retry_action(state: State, query: str) -> tuple[str, str] | None:
    if _looks_like_structured_db_query(query) and not _has_event(state, "db_search"):
        return "db_search", "structured_query_retry_to_db_search"
    if is_web_search_allowed(state) and _looks_like_external_query(query) and not _has_event(state, "web_search"):
        return "web_search", "external_query_retry_to_web_search"
    if _reasoning_attempts(state) >= 1:
        return None
    if should_rewrite_query(query) and not _has_event(state, "rewrite_query"):
        return "rewrite_query", "retry_to_rewrite_query"
    if should_decompose_query(query) and not _has_event(state, "decompose_query"):
        return "decompose_query", "retry_to_decompose_query"
    return None


def agent_node(state: State):
    last_tool = next((event for event in reversed(state.action_history) if event.kind == "tool"), None)
    last_event = state.action_history[-1] if state.action_history else None
    effective_query = state.working_query or state.resolved_query or state.query or ""

    input_guard = guard_input(state.query or effective_query)
    if not input_guard.is_valid:
        return _build_finish_response(
            state,
            answer=input_guard.response or "",
            reason=input_guard.reason or "invalid_input",
            status="failed",
            fail_reason="disallowed_query" if input_guard.reason in DISALLOWED_INPUT_REASONS else "invalid_input",
            diagnostics=state.diagnostics + [f"agent:input_blocked:{input_guard.reason}"],
        )

    if state.current_step >= state.max_steps:
        if _can_finalize(state, allow_partial=True):
            return {
                "action": "finalize",
                "reason": f"Reached max steps: {state.max_steps}",
                "diagnostics": state.diagnostics + ["agent:max_steps_finalize"],
            }
        return _build_finish_response(
            state,
            answer=get_last_answer(last_tool) or build_fallback_answer(state),
            reason=f"Reached max steps: {state.max_steps}",
            status="failed",
            fail_reason="max_steps_exceeded",
            diagnostics=state.diagnostics + ["agent:max_steps_exceeded"],
        )

    if (
        last_event
        and last_event.kind == "tool"
        and getattr(last_event.output, "is_sufficient", False)
        and _can_finalize(state, allow_partial=False)
    ):
        return {
            "action": "finalize",
            "reason": "retrieval_evidence_is_sufficient",
            "diagnostics": state.diagnostics + ["agent:finalize_after_sufficient_evidence"],
        }

    force_finish, finish_reason = should_force_finish(state)
    if force_finish:
        if _can_finalize(state, allow_partial=True):
            return {
                "action": "finalize",
                "reason": finish_reason,
                "diagnostics": state.diagnostics + [f"agent:force_finalize:{finish_reason}"],
            }
        return _build_finish_response(
            state,
            answer=get_last_answer(last_tool) or build_fallback_answer(state),
            reason=finish_reason or "force_finish",
            status="failed",
            fail_reason=getattr(state.last_rag_result, "fail_reason", None) or "insufficient_context",
            diagnostics=state.diagnostics + [f"agent:force_finish:{finish_reason}"],
        )

    reasoning_history = [event for event in state.action_history if event.kind == "reasoning"]
    if not reasoning_history:
        initial_decision = decide_initial_action(state)
        if initial_decision.next_action == "clarify_question":
            return _build_finish_response(
                state,
                answer=initial_decision.clarification_question or "请补充你的问题背景、对象或范围。",
                reason=initial_decision.reason or "clarify_question",
                status="success",
                fail_reason="ambiguous_query",
                diagnostics=state.diagnostics + ["agent:clarify_question"],
            )

        return {
            "action": initial_decision.next_action,
            "reason": initial_decision.reason or "initial_action_selected",
            "diagnostics": state.diagnostics + [f"agent:initial={initial_decision.next_action}"],
        }

    if last_event and last_event.kind == "reasoning":
        action, reason = _select_tool_after_reasoning(state, effective_query)
        return {
            "action": action,
            "reason": reason,
            "diagnostics": state.diagnostics + [f"agent:after_reasoning={action}"],
        }

    if last_tool:
        if last_tool.name == "db_search":
            if _has_finalize_material(state):
                return {
                    "action": "finalize",
                    "reason": "db_search_has_material",
                    "diagnostics": state.diagnostics + ["agent:db_search_finalize"],
                }
            return _build_finish_response(
                state,
                answer=get_last_answer(last_tool) or build_fallback_answer(state),
                reason="db_search_without_material",
                status="failed",
                fail_reason=getattr(last_tool.output, "fail_reason", None) or "no_data",
                diagnostics=state.diagnostics + ["agent:db_search_finish"],
            )

        if last_tool.name in {"rag", "web_search"}:
            if _can_finalize(state, allow_partial=False):
                return {
                    "action": "finalize",
                    "reason": f"{last_tool.name}_has_sufficient_material",
                    "diagnostics": state.diagnostics + [f"agent:{last_tool.name}_finalize"],
                }
            if _has_finalize_material(state):
                return {
                    "action": "finalize",
                    "reason": f"{last_tool.name}_has_partial_material",
                    "diagnostics": state.diagnostics + [f"agent:{last_tool.name}_partial_finalize"],
                }

            retry_action = _select_retry_action(state, effective_query)
            if retry_action:
                action, reason = retry_action
                return {
                    "action": action,
                    "reason": reason,
                    "diagnostics": state.diagnostics + [f"agent:retry={action}"],
                }

            return _build_finish_response(
                state,
                answer=get_last_answer(last_tool) or build_fallback_answer(state),
                reason=f"{last_tool.name}_exhausted",
                status="failed",
                fail_reason=getattr(last_tool.output, "fail_reason", None) or "insufficient_context",
                diagnostics=state.diagnostics + [f"agent:{last_tool.name}_finish"],
            )

    allowed_actions = get_allowed_actions(state)
    fallback_action = allowed_actions[0] if allowed_actions else "finish"
    if fallback_action == "finish" and _can_finalize(state, allow_partial=True):
        fallback_action = "finalize"
    return {
        "action": fallback_action,
        "reason": "deterministic_fallback",
        "diagnostics": state.diagnostics + [f"agent:fallback={fallback_action}"],
    }


def get_last_answer(last_tool) -> str:
    if last_tool and last_tool.output:
        return getattr(last_tool.output, "evidence_summary", None) or getattr(last_tool.output, "answer", "") or ""
    return ""


def build_fallback_answer(state: State) -> str:
    if state.sub_query_results:
        return "已尝试拆解并检索多个子问题，但当前证据仍不足以稳定回答原问题。"
    if state.last_rag_result and state.last_rag_result.fail_reason == "no_data":
        return "当前知识库中未检索到足够相关内容，暂时无法给出可靠答案。"
    return "当前信息不足，暂时无法稳定回答该问题。"

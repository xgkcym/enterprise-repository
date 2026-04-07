import time

from src.models.llm import deepseek_llm
from src.nodes.helpers import build_state_patch, create_event, finalize_event
from src.tools.resolved_query_tool import ResolvedQueryResult, resolved_query_tool
from src.types.agent_state import State
from src.types.base_type import BaseNodeResult
from src.types.event_type import ReasoningEvent


class ResolveQueryNodeResult(BaseNodeResult):
    name: str = "resolved_query"


def resolved_query_node(state: State):
    start_time = time.time()
    resolved = resolved_query_tool(deepseek_llm, state.query or "", state.chat_history)
    query = (resolved.answer or state.query or "").strip()
    event = create_event(
        ReasoningEvent,
        name="resolved_query",
        input_data={"query": state.query},
        max_attempt=1,
    )
    event.attempt = 1
    event = finalize_event(
        event,
        ResolveQueryNodeResult(
            answer=query,
            success=True,
            diagnostics=list(resolved.diagnostics or []),
            message=resolved.message or "resolved query success",
        ),
        start_time,
    )
    return build_state_patch(
        state,
        event,
        resolved_query=query,
        working_query=query,
    )

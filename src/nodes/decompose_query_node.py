import time

from src.agent.policy import should_decompose_query
from src.models.llm import deepseek_llm
from src.nodes.helpers import build_state_patch, create_event, finalize_event, get_next_attempt
from src.tools.decompose_query_tool import DecomposeResult, decompose_query_tool
from src.types.agent_state import State
from src.types.event_type import ReasoningEvent


def decompose_query_node(state: State):
    query = state.working_query or state.resolved_query or state.query or ""
    start_time = time.time()
    event = create_event(
        ReasoningEvent,
        name="decompose_query",
        input_data={"query": query},
        max_attempt=1,
    )

    if should_decompose_query(query):
        decompose_query = decompose_query_tool(deepseek_llm, query, state.chat_history)
    else:
        decompose_query = DecomposeResult(
            answer=[],
            success=True,
            name="decompose_query",
            message="decompose query skipped",
            diagnostics=["decompose_query_skipped_not_complex"],
        )

    event.attempt = get_next_attempt(state.action_history, "decompose_query")
    event = finalize_event(event, decompose_query, start_time)
    return build_state_patch(
        state,
        event,
        working_query=query,
        decompose_query=decompose_query.answer,
    )

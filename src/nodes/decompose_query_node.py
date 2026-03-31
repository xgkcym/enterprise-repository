from src.models.llm import deepseek_llm
from src.tools.decompose_query_tool import decompose_query_tool
from src.types.agent_state import State
from src.types.event_type import ReasoningEvent


def decompose_query_node(state:State):
    event = ReasoningEvent(
        name="decompose_query",
        input={"query": state.working_query},
        max_attempt=1
    )
    decompose_query = decompose_query_tool(deepseek_llm,state.working_query,state.chat_history)
    last_event = next((event for event in reversed(state.action_history) if event.name == "decompose_query"),None)
    if  last_event:
        event.attempt = last_event.attempt + 1
    else:
        event.attempt = 1


    event.output = decompose_query
    return {
        "working_query":"|".join(decompose_query.answer),
        "decompose_query":decompose_query.answer,
        "action_history": state.action_history + [event],
    }

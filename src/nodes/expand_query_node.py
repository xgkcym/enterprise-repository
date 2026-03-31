from src.models.llm import deepseek_llm
from src.tools.expand_query_tool import expand_query_tool
from src.types.agent_state import State
from src.types.event_type import ReasoningEvent


def expand_query_node(state:State):
    event = ReasoningEvent(
        name="expand_query",
        input={"query":state.working_query or  state.query},
        max_attempt=1
    )
    expand_query = expand_query_tool(deepseek_llm,state.working_query,state.chat_history)
    last_event = next((event for event in state.action_history[::-1] if event.name == "expand_query"),None)
    if  last_event:
        event.attempt = last_event.attempt + 1
    else:
        event.attempt = 1
    event.output = expand_query
    return {
        "working_query":"|".join(expand_query.answer),
        "expand_query":expand_query.answer,
        "action_history": state.action_history + [event],
    }
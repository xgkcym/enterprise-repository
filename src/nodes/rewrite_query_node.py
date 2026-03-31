from src.models.llm import deepseek_llm
from src.tools.rewrite_query_tool import rewrite_query_tool, RewriteResult
from src.types.agent_state import State
from src.types.event_type import ReasoningEvent


def rewrite_query_node(state:State):
    query = state.working_query or state.query
    reasoning_event = ReasoningEvent(
        name="rewrite_query",
        input={"query": query},
    )
    if len(query) > 10:
        rewritten:RewriteResult = rewrite_query_tool(deepseek_llm,state.working_query,state.chat_history)
    else:
        rewritten = RewriteResult(
            answer=query,
        )
    last_event = next((event for event in state.action_history[::-1] if event.name == "rewrite_query"),None)
    if  last_event:
        reasoning_event.attempt = last_event.attempt + 1
    else:
        reasoning_event.attempt = 1
    reasoning_event.input = {"query": query}
    reasoning_event.output = rewritten
    return {
        "working_query":rewritten.answer,
        "rewrite_query":rewritten.answer,
        "action_history": state.action_history + [reasoning_event],
    }
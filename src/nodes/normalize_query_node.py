from src.types.agent_state import State

from src.tools.normalize_query_tool import normalize_query
from src.types.base_type import  BaseToolResult
from src.types.event_type import ReasoningEvent


class NormalizeQueryResult(BaseToolResult):
    pass

def normalize_query_node(state:State):
    query = normalize_query(state.query)
    return {
        "query":query,
        "working_query":query,
        "action_history": state.action_history + [ReasoningEvent(
            name="normalize_query",
            input={"query": state.query},
            output=NormalizeQueryResult(answer=query),
            attempt=1,
            max_attempt=1
        )],
    }
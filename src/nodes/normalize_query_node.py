from src.types.agent_state import State

from src.tools.normalize_query_tool import normalize_query


def normalize_query_node(state:State):
    query = normalize_query(state.query)
    state.rag_context.query = query
    return {"query":query,"rag_context":state.rag_context}
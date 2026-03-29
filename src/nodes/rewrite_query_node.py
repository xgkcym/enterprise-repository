from src.models.llm import deepseek_llm
from src.tools.rewrite_query_tool import rewrite_query_tool
from src.types.agent_state import State


def rewrite_query_node(state:State):
    query = state.query
    if len(query) < 20:
        rewritten = rewrite_query_tool(deepseek_llm,state.query,state.chat_history)
    else:
        rewritten = state.query
    state.rag_context.rewritten_query = rewritten
    return {
        "rewritten_query": rewritten,
        "rag_context":state.rag_context
    }
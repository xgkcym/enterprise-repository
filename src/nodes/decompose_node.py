from src.models.llm import deepseek_llm
from src.tools.decompose_query_tool import decompose_query_tool
from src.types.agent_state import State


def decompose_node(state:State):
    expand_query = decompose_query_tool(deepseek_llm,state.query,state.chat_history)
    return {"expand_query":expand_query}

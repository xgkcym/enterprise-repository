from src.models.llm import deepseek_llm
from src.tools.rewrite_query_tool import rewrite_query_tool, RewriteResult
from src.types.agent_state import State
from src.types.base_type import ToolEvent


def rewrite_query_node(state:State):
    query = state.working_query or state.query
    if len(query) > 10:
        rewritten:RewriteResult = rewrite_query_tool(deepseek_llm,state.working_query,state.chat_history)
    else:
        rewritten = RewriteResult(
            answer=query,
        )

    print(f"重写之前:{query}")
    print(f"重写查询:{rewritten.answer}")
    return {
        "working_query":rewritten.answer,
        "query_used":False,
        "rewrite_attempt": state.rewrite_attempt + 1,
    }
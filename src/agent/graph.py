from langgraph.constants import END
from langgraph.graph import StateGraph

from src.nodes.decompose_node import decompose_node
from src.nodes.expand_node import expand_node
from src.nodes.normalize_query_node import normalize_query_node
from src.nodes.rag_node import rag_node
from src.nodes.rewrite_query_node import rewrite_query_node
from src.router.index import  route_map
from src.types.agent_state import State

builder = StateGraph(State)


builder.add_node("normalize_query", normalize_query_node)
builder.set_entry_point("normalize_query")

builder.add_node("rewrite_query", rewrite_query_node)
builder.add_node("expand_query", expand_node)
builder.add_node("decompose_query", decompose_node)

builder.add_node("rag", rag_node)
builder.add_edge("normalize_query", "rag")
builder.add_edge("rewrite_query", "rag")
builder.add_edge("expand_query", "rag")
builder.add_edge("decompose_query", "rag")



# 条件分支：决定是否 rewrite
def route(state:State):
    # 动态跳转根据 Agent 决策输出
    action_map = {
        **route_map,
    }
    return action_map.get(state.action, END)
builder.add_conditional_edges(
    "rag",
    route,
    { **route_map }
)





graph = builder.compile()


if __name__ == '__main__':
    print(graph.invoke(State(query="什么是金融知识？")))
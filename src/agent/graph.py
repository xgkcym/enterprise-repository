from langgraph.constants import END
from langgraph.graph import StateGraph

from src.nodes.agent_node import agent_node
from src.nodes.rag_node import rag_node
from src.nodes.rewrite_query_node import rewrite_query_node
from src.router.index import route_map
from src.types.agent_state import State

builder = StateGraph(State)


def route(state:State):
    # 动态跳转根据 Agent 决策输出
    return route_map.get(state.action, END)

builder.add_node("agent", agent_node)
builder.set_entry_point("agent")
builder.add_node("rewrite_query", rewrite_query_node)
builder.add_node("rag", rag_node)


builder.add_edge("rag", "agent")
builder.add_edge("rewrite_query", "agent")


builder.add_conditional_edges(
    'agent',
    route,
)

graph = builder.compile()


if __name__ == '__main__':
    print(graph.invoke(State(query="什么是金融里面包含什么样的知识，又怎么学？")))
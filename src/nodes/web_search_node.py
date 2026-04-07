import time

from src.nodes.helpers import build_state_patch, create_event, finalize_event, get_next_attempt
from src.tools.web_search_tool import web_search_tool
from src.types.agent_state import State
from src.types.event_type import ToolEvent
from src.types.web_search_type import WebSearchContext


def web_search_node(state: State):
    """执行网络搜索的节点函数

    根据给定的状态信息构建搜索上下文，执行网络搜索，并返回更新后的状态

    Args:
        state (State): 包含查询信息、RAG上下文等的当前状态对象

    Returns:
        dict: 包含更新后的工具事件、RAG结果等信息的状态补丁
    """
    effective_query = state.working_query or state.resolved_query or state.query or ""

    # 记录开始时间用于计算执行耗时
    start_time = time.time()
    # 创建工具事件对象
    new_tool = create_event(ToolEvent, name="web_search")

    # 构建网络搜索上下文
    web_context = WebSearchContext(
        query=effective_query,
        rewritten_query=state.rewrite_query,  # 重写后的查询
        expand_query=state.expand_query,  # 扩展后的查询
        decompose_query=state.decompose_query,  # 分解后的查询
        # 设置检索结果数量，范围限制在3-10之间，若没有上下文则默认为5
        retrieval_top_k=max(3, min(state.last_rag_context.retrieval_top_k, 10))
        if state.last_rag_context
        else 5,
        # 设置搜索计数，与retrieval_top_k保持一致
        count=max(3, min(state.last_rag_context.retrieval_top_k, 10))
        if state.last_rag_context
        else 5,
    )

    # 执行网络搜索工具
    tool_result = web_search_tool(web_context)
    # 设置当前尝试次数
    new_tool.attempt = get_next_attempt(state.action_history, "web_search")
    # 记录搜索输入上下文
    new_tool.input = web_context
    # 完成事件记录，包括执行结果和耗时
    new_tool = finalize_event(new_tool, tool_result, start_time)

    # 构建并返回状态补丁
    return build_state_patch(
        state,
        new_tool,  # 新的工具事件
        last_rag_result=tool_result,  # 最新的RAG结果
        answer=state.answer,  # 保持原答案
        citations=state.citations,  # 保持原引用
    )

import time

from src.nodes.helpers import build_state_patch, create_event, finalize_event, get_next_attempt
from src.tools.db_search_tool import db_search_tool
from src.types.agent_state import State
from src.types.db_search_type import DBSearchContext
from src.types.event_type import ToolEvent


def db_search_node(state: State):
    """数据库搜索节点

    根据给定的状态信息执行数据库搜索操作，并返回更新后的状态

    Args:
        state: 包含用户查询、个人信息等状态信息

    Returns:
        返回更新后的状态补丁，包含搜索结果等信息
    """
    # 记录操作开始时间
    start_time = time.time()
    # 创建数据库搜索工具事件
    new_tool = create_event(ToolEvent, name="db_search")
    # 获取用户信息，若不存在则使用空字典
    profile = state.user_profile or {}

    # 构建数据库搜索上下文
    db_context = DBSearchContext(
        query=state.query,  # 原始查询
        rewritten_query=state.rewrite_query,  # 重写后的查询
        user_id=profile.get("user_id"),  # 用户ID
        role_id=profile.get("role_id"),  # 角色ID
        # 部门ID，支持两种字段名(dept_id/department_id)
        department_id=profile.get("department_id") or profile.get("dept_id"),
        # 允许访问的部门ID列表，确保为列表类型
        allowed_department_ids=list(profile.get("allowed_department_ids") or []),
        limit=5,  # 结果数量限制
    )

    # 执行数据库搜索工具
    tool_result = db_search_tool(db_context)
    # 设置当前尝试次数
    new_tool.attempt = get_next_attempt(state.action_history, "db_search")
    # 记录搜索输入参数
    new_tool.input = db_context
    # 完成事件记录，包含耗时等信息
    new_tool = finalize_event(new_tool, tool_result, start_time)

    # 构建并返回状态补丁
    return build_state_patch(
        state,
        new_tool,  # 工具事件
        last_rag_result=tool_result,  # 搜索结果
        answer=state.answer,  # 保留原回答
        citations=state.citations,  # 保留原引用
    )

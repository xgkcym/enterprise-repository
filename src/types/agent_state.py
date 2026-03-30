from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

from src.types.base_type import ToolEvent


class State(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,  # 赋值时验证类型
        extra="forbid"  # 禁止额外字段，防止拼写错误
    )
    query: Optional[str]

    working_query: Optional[str] = Field(default="",description="当前工作查询")

    rewrite_attempt: int = Field(default=0,description="重写查询尝试次数")

    # rewritten_query: Optional[str] = Field(default="",description="重写查询")
    #
    # expand_query:List[str] = Field(default=[],description="拓展查询")
    #
    # decompose_query:List[str] = Field(default=[],description="子任务规划")

    answer:  Optional[str] = Field(default="",description="回答")

    chat_history:List[str] = Field(default=[],description="短期记忆")

    user_profile:Optional[Dict[str, Any]] = Field(default=None,description="用户画像")

    reason:Optional[str] = Field(default="",description="推断结果")

    current_input:Optional[Any] = Field(default=None,description="当前输入")

    tool_history:List[ToolEvent] = Field(default=[],description="工具调用历史")

    query_used:bool = Field(default=False,description="当前查询是否已经被用于检索")

    last_action: Optional[str] = Field(default="",description="上一步行动")

    action:Optional[str] = Field(default="",description="下一步行动")
from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

from src.types.event_type import Event


class State(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,  # 赋值时验证类型
        extra="forbid"  # 禁止额外字段，防止拼写错误
    )
    query: Optional[str]

    working_query: Optional[str] = Field(default="",description="当前工作查询")

    rewrite_query: Optional[str] = Field(default="",description="重写查询")

    expand_query:Optional[List[str]] = Field(default=None,description="拓展查询")

    decompose_query:Optional[List[str]] = Field(default=None,description="子任务规划")


    answer:  Optional[str] = Field(default="",description="回答")

    chat_history:List[str] = Field(default=[],description="短期记忆")

    user_profile:Optional[Dict[str, Any]] = Field(default=None,description="用户画像")

    reason:Optional[str] = Field(default="",description="推断结果")

    action_history:List[Event] = Field(default=[],description="行动调用历史")

    action:Optional[str] = Field(default="",description="下一步行动")
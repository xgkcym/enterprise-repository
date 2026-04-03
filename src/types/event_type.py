from uuid import uuid4
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from src.types.base_type import BaseResult


EventKind = Literal["tool", "reasoning", "memory", "guardrail"]
EventStatus = Literal["pending", "success", "failed"]


class BaseEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="事件ID")
    kind: EventKind = Field(default="tool", description="事件类型")
    name: str = Field(default="", description="事件名称")
    status: EventStatus = Field(default="pending", description="事件状态")
    input: Optional[Any] = Field(default=None, description="请求参数")
    output: Optional[BaseResult] = Field(default=None, description="返回参数")
    started_at: Optional[str] = Field(default=None, description="开始时间")
    ended_at: Optional[str] = Field(default=None, description="结束时间")
    duration: Optional[int] = Field(default=None, description="耗时")
    attempt: int = Field(default=0, description="调用次数")
    max_attempt: int = Field(default=3, description="最大调用次数")
    error: Optional[str] = Field(default=None, description="错误信息")


class ToolEvent(BaseEvent):
    kind: Literal["tool"] = Field(default="tool", description="事件类型")


class ReasoningEvent(BaseEvent):
    kind: Literal["reasoning"] = Field(default="reasoning", description="事件类型")


class MemoryEvent(BaseEvent):
    kind: Literal["memory"] = Field(default="memory", description="事件类型")


class GuardrailEvent(BaseEvent):
    kind: Literal["guardrail"] = Field(default="guardrail", description="事件类型")

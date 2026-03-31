from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, Field

from src.types.base_type import BaseToolResult
from src.types.rag_type import RAGResult


class Event(BaseModel):
    kind: Literal["tool", "reasoning"] = Field(default="tool", description="事件类型")
    name: Optional[str] = Field(default="", description="事件名称")
    input: Optional[Any] = Field(default=None, description="请求参数")
    output: Optional[BaseToolResult | RAGResult | Any] = Field(default=None, description="返回参数")
    attempt: Optional[int] = Field(default=0, description="调用次数")
    max_attempt: Optional[int] = Field(default=3, description="最大调用次数")


class ToolEvent(Event):
    kind:str = Field(default="tool",description="事件类型")

class ReasoningEvent(Event):
    kind:str = Field(default="reasoning",description="事件类型")
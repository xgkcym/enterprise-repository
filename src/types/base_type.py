from typing import Any, Optional

from pydantic import BaseModel, Field


class BaseResult(BaseModel):
    success: bool = Field(default=False, description="是否成功")
    message: Optional[str] = Field(default="", description="消息")
    error_code: str | None = Field(default=None, description="错误码")
    error_detail: str | None = Field(default=None, description="错误详情")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")


class BaseNodeResult(BaseResult):
    """给 reasoning node 用"""

    answer: Optional[Any] = Field(default=None, description="回答")


class BaseToolResult(BaseResult):
    answer: Optional[Any] = Field(default=None, description="回答")
    is_sufficient: bool = Field(default=False, description="是否足够回答")
    reason: Optional[str] = Field(default=None, description="诊断理由")


class BaseLLMDecideResult(BaseResult):
    """LLM 诊断返回的数据"""

    reason: Optional[str] = Field(default=None, description="诊断信息")
    confidence: Optional[float] = Field(default=None, description="置信度")
    next_action: Optional[str] = Field(default=None, description="下一步路由")

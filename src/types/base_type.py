from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, Field


class BaseToolResult(BaseModel):
    # ===== 最终输出 =====
    answer: Optional[Any] = Field(default=None, description="回答")

    # ===== 诊断信息（给Agent用）=====
    is_sufficient: bool = Field(default=False, description="是否足够回答")

    reason:Optional[str] = Field(default=None,description="诊断理由")




class BaseLLMDecideResult(BaseModel):
    """LLM诊断返回的数据"""

    reason:Optional[str] =  Field(default=None,description="诊断信息")
    next_action:Optional[str] = Field(default=None,description="下一步路由")







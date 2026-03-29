from typing import Optional, List

from pydantic import BaseModel, Field



class BaseToolResult(BaseModel):
    tool_name: Optional[str] = Field(default=None,description="工具名称")

    attempt: Optional[int] = Field(default=0, description="调用次数")

    # ===== 最终输出 =====
    answer: Optional[str] = Field(default="", description="回答")

    # ===== 诊断信息（给Agent用）=====
    is_sufficient: bool = Field(default=False, description="是否足够回答")

    reason:Optional[str] = Field(default=None,description="诊断理由")

    citations: List[str] = Field(default=[], description="生成答案中引用")

    # ===== 检索信息 =====
    documents: List[any] = Field(default=[], description="检索到的文档")

    previous_fail_reason: Optional[str] = Field(default=[], description="历史信息")

class BaseLLMDecideResult(BaseModel):
    """LLM诊断返回的数据"""
    # ===== 质量评估（核心）=====
    confidence: float = Field(default=0.0, description="0~1（模型或规则估计）")
    coverage: float = Field(default=0.0, description="覆盖度（是否回答完整）")
    fail_reason:Optional[str] =  Field(default=None,description="诊断信息")
    suggested_actions:List[str] = Field(default=None,description="行为建议")
    next_action:Optional[str] = Field(default=None,description="下一步路由")
from typing import Optional

from pydantic import BaseModel, Field

from src.types.base_type import BaseLLMDecideResult


class InputGuardDecision(BaseModel):
    is_valid: bool = Field(default=True, description="输入是否可以继续处理")
    reason: Optional[str] = Field(default=None, description="输入被阻断的原因")
    response: Optional[str] = Field(default=None, description="面向用户的阻断提示")


class InitialActionDecision(BaseModel):
    next_action: str = Field(default="rag", description="策略建议的初始动作")
    reason: Optional[str] = Field(default=None, description="策略原因")
    clarification_question: Optional[str] = Field(default=None, description="需要澄清时的问题")


class RetrievalPolicyPlan(BaseModel):
    retrieval_top_k: int = Field(default=0, description="检索器 top-k")
    rerank_top_k: int = Field(default=0, description="重排序器 top-k")
    use_retrieval: bool = Field(default=True, description="是否执行检索")
    use_rerank: bool = Field(default=True, description="是否执行重排序")
    needs_more_recall: bool = Field(default=False, description="是否需要提高召回")
    needs_more_precision: bool = Field(default=False, description="是否需要提高精度")
    strategy_reason: Optional[str] = Field(default=None, description="检索策略原因")


class AgentPlannerStructuredDecision(BaseModel):
    next_action: str = Field(default="finish", description="规划器选择的动作")
    reason: Optional[str] = Field(default=None, description="选择该动作的原因")
    confidence: Optional[float] = Field(default=None, description="规划器置信度")
    clarification_question: Optional[str] = Field(default=None, description="需要澄清时的问题")


class AgentPlannerDecision(BaseLLMDecideResult):
    next_action: str = Field(default="finish", description="规划器选择的动作")
    clarification_question: Optional[str] = Field(default=None, description="需要澄清时的问题")

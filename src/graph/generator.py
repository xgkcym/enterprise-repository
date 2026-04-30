from __future__ import annotations

from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, ConfigDict, Field

from src.config.llm_config import LLMService
from src.prompts.graph import FINANCIAL_GRAPH_ANSWER_PROMPT


def _format_list(values: list[str] | None) -> str:
    items = [str(item).strip() for item in values or [] if str(item).strip()]
    if not items:
        return "(none)"
    return ", ".join(items)


class FinancialGraphAnswerResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(default="", description="面向用户的简短回答")
    evidence_summary: str = Field(default="", description="基于证据的说明")
    citations: list[str] = Field(default_factory=list, description="引用节点 ID")
    is_sufficient: bool = Field(default=False, description="证据是否充分")
    fail_reason: Literal[
        "low_recall",
        "bad_ranking",
        "ambiguous_query",
        "no_data",
        "insufficient_context",
    ] | None = Field(default=None, description="证据不足时的失败原因")
    reason: str = Field(default="", description="简短的模型侧推理轨迹")


def generate_financial_graph_answer(
    llm: BaseChatModel,
    *,
    query: str,
    context: str,
    query_kind: str,
    comparison_mode: bool,
    metric_names: list[str] | None = None,
    topics: list[str] | None = None,
    years: list[str] | None = None,
    company_terms: list[str] | None = None,
    allowed_citations: list[str] | None = None,
) -> FinancialGraphAnswerResult:
    prompt = FINANCIAL_GRAPH_ANSWER_PROMPT.format(
        query=query or "",
        query_kind=query_kind or "general",
        comparison_mode=str(bool(comparison_mode)).lower(),
        metric_names=_format_list(metric_names),
        topics=_format_list(topics),
        years=_format_list(years),
        company_terms=_format_list(company_terms),
        allowed_citations=_format_list(allowed_citations),
        context=context or "",
    )
    response: FinancialGraphAnswerResult = LLMService.invoke(
        llm=llm,
        messages=[HumanMessage(content=prompt)],
        schema=FinancialGraphAnswerResult,
    )
    return response

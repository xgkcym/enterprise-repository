from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import Field

from src.config.llm_config import LLMService
from src.prompts.agent.resolved_query_prompt import RESOLVED_QUERY_PROMPT
from src.types.base_type import BaseNodeResult


class ResolvedQueryResult(BaseNodeResult):
    name: Optional[str] = Field(default="resolved_query", description="工具名称")
    max_attempt: Optional[int] = Field(default=1, description="最大调用次数")
    answer: Optional[str] = Field(default="", description="解析后的查询")


def _resolved_query(query: str) -> str:
    if not query:
        return ""
    return query.strip().lower()


def resolved_query_tool(
    llm: BaseChatModel,
    query: str,
    chat_history=None,
) -> ResolvedQueryResult:
    normalized_query = _resolved_query(query)
    prompt = RESOLVED_QUERY_PROMPT.format(
        query=normalized_query,
        chat_history=chat_history or [],
    )

    if not chat_history:
        return ResolvedQueryResult(
            answer=normalized_query,
            success=True,
            name="resolved_query",
            message="resolved query without chat history",
            diagnostics=["resolved_query_no_history"],
        )

    try:
        response: ResolvedQueryResult = LLMService.invoke(
            llm=llm,
            messages=[HumanMessage(content=prompt)],
            schema=ResolvedQueryResult,
        )
        response.success = True
        response.name = "resolved_query"
        response.answer = (response.answer or normalized_query).strip()
        response.message = "resolved query success"
        response.diagnostics = list(response.diagnostics or []) + ["resolved_query_completed"]
        return response
    except Exception as exc:
        return ResolvedQueryResult(
            answer=normalized_query,
            success=False,
            name="resolved_query",
            message="resolved query failed",
            error_detail=str(exc),
            diagnostics=["resolved_query_failed"],
        )

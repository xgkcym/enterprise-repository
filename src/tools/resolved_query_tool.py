from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import Field

from src.agent.profile_utils import build_preferred_topics_note
from src.config.llm_config import LLMService
from src.prompts.agent.resolved_query_prompt import RESOLVED_QUERY_PROMPT
from src.types.base_type import BaseNodeResult


class ResolvedQueryResult(BaseNodeResult):
    name: Optional[str] = Field(default="resolved_query", description="tool name")
    max_attempt: Optional[int] = Field(default=1, description="max attempts")
    answer: Optional[str] = Field(default="", description="resolved query")


def _resolved_query(query: str) -> str:
    if not query:
        return ""
    return query.strip().lower()


def resolved_query_tool(
    llm: BaseChatModel,
    query: str,
    chat_history=None,
    user_profile=None,
) -> ResolvedQueryResult:
    normalized_query = _resolved_query(query)
    prompt = RESOLVED_QUERY_PROMPT.format(
        query=normalized_query,
        chat_history=chat_history or [],
    )
    preferred_topics_note = build_preferred_topics_note(user_profile)
    if preferred_topics_note:
        prompt = f"{prompt}\n\n{preferred_topics_note}"

    if not chat_history:
        diagnostics = ["resolved_query_no_history"]
        if preferred_topics_note:
            diagnostics.append("preferred_topics_hint_available:resolved_query")
        return ResolvedQueryResult(
            answer=normalized_query,
            success=True,
            name="resolved_query",
            message="resolved query without chat history",
            diagnostics=diagnostics,
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
        if preferred_topics_note:
            response.diagnostics.append("preferred_topics_hint_applied:resolved_query")
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

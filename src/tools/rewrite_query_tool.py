from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import Field

from src.agent.profile_utils import build_preferred_topics_note
from src.config.llm_config import LLMService
from src.prompts.agent.rewrite_prompt import REWRITE_PROMPT
from src.types.base_type import BaseNodeResult


class RewriteResult(BaseNodeResult):
    name: Optional[str] = Field(default="rewrite_query", description="tool name")
    max_attempt: Optional[int] = Field(default=2, description="max attempts")
    answer: Optional[str] = Field(default="", description="rewritten query")


def rewrite_query_tool(
    llm: BaseChatModel,
    query: str,
    chat_history=None,
    user_profile=None,
) -> RewriteResult:
    prompt = REWRITE_PROMPT.format(
        query=query,
        chat_history=chat_history or [],
    )
    preferred_topics_note = build_preferred_topics_note(user_profile)
    if preferred_topics_note:
        prompt = f"{prompt}\n\n{preferred_topics_note}"

    try:
        response: RewriteResult = LLMService.invoke(
            llm=llm,
            messages=[HumanMessage(content=prompt)],
            schema=RewriteResult,
        )
        response.success = True
        response.name = "rewrite_query"
        response.answer = (response.answer or query or "").strip()
        response.message = "rewrite query success"
        response.diagnostics = list(response.diagnostics or []) + ["rewrite_query_completed"]
        if preferred_topics_note:
            response.diagnostics.append("preferred_topics_hint_applied:rewrite_query")
        return response
    except Exception as exc:
        return RewriteResult(
            answer=(query or "").strip(),
            success=False,
            name="rewrite_query",
            message="rewrite query failed",
            error_detail=str(exc),
            diagnostics=["rewrite_query_failed"],
        )

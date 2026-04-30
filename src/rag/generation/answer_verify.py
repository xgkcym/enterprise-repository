from __future__ import annotations

from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.config.llm_config import LLMService
from src.prompts.rag.answer_verify import VERIFY_PROMPT


class AnswerVerifyResult(BaseModel):
    valid: bool = Field(..., description="答案是否完全由上下文支持")
    reason: Optional[str] = Field(default=None, description="答案通过或失败的原因")


def verify_answer(llm: BaseChatModel, context: str, answer: str) -> AnswerVerifyResult:
    prompt = VERIFY_PROMPT.format(
        context=context,
        answer=answer,
    )

    return LLMService.invoke(
        llm=llm,
        messages=[HumanMessage(content=prompt)],
        schema=AnswerVerifyResult,
    )

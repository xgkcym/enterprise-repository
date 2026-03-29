from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.congfig.llm_config import LLMService
from src.prompts.rag.answer_verify import VERIFY_PROMPT


class AnswerVerifyResult(BaseModel):
    """
        验证回答是否正确
    """
    valid: bool = Field(...,description="回答是否正确")
    reason:Optional[str] = Field(...,description="理由")

def verify_answer(llm:BaseChatModel, context, answer):

    prompt = VERIFY_PROMPT.format(
        context=context,
        answer=answer
    )

    result:AnswerVerifyResult = LLMService.invoke(
        llm=llm,
        messages=[HumanMessage(content=prompt)],
        schema=AnswerVerifyResult
    )

    return result.valid
from typing import List

from langchain_core.messages import HumanMessage
from langchain_openai.chat_models.base import BaseChatOpenAI
from pydantic import BaseModel, Field

from core.settings import settings
from src.congfig.llm_config import LLMService
from src.prompts.rag.decompose import DECOMPOSE_PROMPT



class DecomposeResult(BaseModel):
    """
       问题拆解助手返回的数据
    """
    sub_queries:List[str] = Field(...,description="子问题列表")

def decompose_query(llm:BaseChatOpenAI, query: str, chat_history=None):

    prompt = DECOMPOSE_PROMPT.format(query=query,chat_history=chat_history or [])

    try:
        response: DecomposeResult = LLMService.invoke(
            llm=llm,
            messages=[HumanMessage(content=prompt)],
            schema=DecomposeResult
        )

        return response.sub_queries
    except Exception:
        return []


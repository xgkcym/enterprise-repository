from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.congfig.llm_config import LLMService
from src.types.base_type import BaseNodeResult
from src.prompts.agent.decompose import DECOMPOSE_PROMPT


class DecomposeResult(BaseNodeResult):
    """
       问题拆解助手返回的数据
    """

def decompose_query_tool(llm:BaseChatModel, query: str, chat_history=None):
    prompt = DECOMPOSE_PROMPT.format(query=query, chat_history=chat_history or [])
    try:
        response: DecomposeResult = LLMService.invoke(
            llm=llm,
            messages=[HumanMessage(content=prompt)],
            schema=DecomposeResult
        )
        response.success = True
        return response
    except Exception:
        return DecomposeResult(
            answer=[],
            success=False,
        )

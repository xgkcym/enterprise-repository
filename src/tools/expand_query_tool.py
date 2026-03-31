from typing import List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.congfig.llm_config import LLMService
from src.prompts.agent.expand import EXPAND_PROMPT
from src.types.base_type import BaseToolResult


class ExpandResult(BaseToolResult):
    """
       查询扩展助手返回的数据
    """
    pass
def expand_query_tool(llm:BaseChatModel, query: str, chat_history=None):

    prompt = EXPAND_PROMPT.format(query=query, chat_history=chat_history or [])

    try:
        response: ExpandResult = LLMService.invoke(
            llm=llm,
            messages=[HumanMessage(content=prompt)],
            schema=ExpandResult
        )
        response.is_sufficient = True
        return response
    except Exception:
        return ExpandResult(
            is_sufficient=False,
            answer=[],
        )

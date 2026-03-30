from typing import List, Dict, Literal, Optional

from anthropic import BaseModel
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import Field
from src.congfig.llm_config import LLMService
from src.prompts.agent.rewrite_prompt import REWRITE_PROMPT
from src.types.base_type import BaseToolResult


class RewriteResult(BaseToolResult):
    """
       Query优化助手返回的数据
    """
    tool_name:Optional[str] = Field(default="rewrite_query",description="工具名称")
    max_attempt:Optional[int] = Field(default=2, description="最大调用次数")



def rewrite_query_tool(llm:BaseChatModel,query:str,chat_history=None,user_profile=None)->RewriteResult:
    """对输入的数据进行一个同义词替换、易检索更改"""
    prompt = REWRITE_PROMPT.format(
        query=query,
        chat_history=chat_history or []
    )
    try:
        response: RewriteResult = LLMService.invoke(
            llm=llm,
            messages=[HumanMessage(content=prompt)],
            schema=RewriteResult
        )
        response.is_sufficient = response.answer == query
        return response
    except Exception:
        return RewriteResult(
            answer=query,
            is_sufficient=False,
        )


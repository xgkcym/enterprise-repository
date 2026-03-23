import json
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_openai.chat_models.base import BaseChatOpenAI
from pydantic import BaseModel, Field

from core.settings import settings
from src.congfig.llm_config import LLMService
from src.models.llm import deepseek_llm
from src.prompts.rag.rewrite_prompt import REWRITE_PROMPT
from src.rag.models import QueryResult




class RewriteResult(BaseModel):
    """
        Query优化助手返回的数据
    """
    rewrite_query: str = Field(...,description="原始语言")
    chinese_query: str = Field(...,description="中文语言")
    english_query: str = Field(...,description="英语语言")
    intent: Literal["factoid", "analysis", "comparison"] = Field(...,description="意图")


def rewrite(llm:BaseChatOpenAI, query: str, chat_history=None):

    prompt = REWRITE_PROMPT.format(
        query=query,
        chat_history=chat_history or []
    )
    try:
        response:RewriteResult = LLMService.invoke(
            llm=llm,
            messages=[HumanMessage(content=prompt)],
            schema=RewriteResult
        )
        rewrite_query = response.rewrite_query
        chinese_query = response.chinese_query
        english_query = response.english_query
        intent = response.intent

        search_queries = [rewrite_query]

        if english_query:
            search_queries.append(english_query)
        if chinese_query:
            search_queries.append(chinese_query)

        return QueryResult(
            rewrite_query=rewrite_query,
            search_queries=list(set(search_queries)),
            filters={},
            intent=intent
        )

    except Exception:
        return QueryResult(
            rewrite_query=query,
            search_queries=[query],
            filters={},
            intent="factoid"
        )

if __name__ == "__main__":
    print(rewrite(deepseek_llm, "请问你是谁"))
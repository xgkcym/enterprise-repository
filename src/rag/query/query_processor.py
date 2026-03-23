from typing import List, Dict, Literal

from langchain_openai.chat_models.base import BaseChatOpenAI
from pydantic import BaseModel, Field

from core.settings import settings
from src.models.llm import deepseek_llm
from src.rag.models import QueryResult
from src.rag.query.decompose import decompose_query
from src.rag.query.expand import expand_query
from src.rag.query.normalize import normalize_query
from src.rag.query.rewrite import rewrite





class QueryProcessor:

    def __init__(self,llm:BaseChatOpenAI):
        self.llm = llm


    def run(self, query, chat_history=None, user_profile=None):
        """清洗输入、重写输入"""

        #清洗输入
        query = normalize_query(query)

        #重写输入
        print("📝重写输入")
        rewrite_result: QueryResult = rewrite(self.llm, query, chat_history)

        expand_queries = []
        decompose_queries = []
        if rewrite_result.intent == "factoid":
            #事实查询 拓展
            # 查询拓展
            print("🧾拓展查询")
            expand_queries = expand_query(self.llm, rewrite_result.rewrite_query)
            pass
        elif rewrite_result.intent == "analysis":
            # 分析 拓展+问题拆分
            # 查询拓展
            print("🧾拓展查询")
            expand_queries = expand_query(self.llm, rewrite_result.rewrite_query)
            # 问题拆分
            print("🎁问题拆分")
            decompose_queries = decompose_query(self.llm, rewrite_result.rewrite_query)
        elif rewrite_result.intent == "comparison":
            # 对比 问题拆分
            # 问题拆分
            print("🎁问题拆分")
            decompose_queries = decompose_query(self.llm, rewrite_result.rewrite_query)

        print(expand_queries)

        # 合并
        search_queries = list(set(
            rewrite_result.search_queries + expand_queries[:settings.max_expand] + decompose_queries
        ))


        return QueryResult(
            rewrite_query=rewrite_result.rewrite_query,
            search_queries=search_queries,
            filters=rewrite_result.filters,
            intent=rewrite_result.intent
        )
query_processor = QueryProcessor(deepseek_llm)


if  __name__ == "__main__":
    res = query_processor.run("请你帮我分析一下永动机的是否可以创造出来？")
    print(res)
    print(res.search_queries)


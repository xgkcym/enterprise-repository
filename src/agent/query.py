from typing import List, Dict

from pydantic import BaseModel

from src.prompts.agent_query import agent_query_prompt
import json


class QueryAgentOutput(BaseModel):
    rewrite_query: str
    search_queries: List[str]
    intent: str
    filters: Dict[str, str]
    confidence: float
    rewrite_query:str
    search_queries:List[str]


class QueryAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, query, chat_history=None, user_profile=None):
        prompt = agent_query_prompt(query, chat_history, user_profile)

        response = self.llm.invoke(prompt)
        # ⚠️ 企业级必须做：JSON解析保护
        return self.parse_output(response)

    def parse_output(self, response):
        try:
            data = json.loads(response)
            return QueryAgentOutput(**data)
        except Exception:
            # fallback（非常关键）
            return QueryAgentOutput(
                rewrite_query=response,
                search_queries=[response],
                intent="factoid",
                filters={},
                confidence=0.3,
                rewrite_query=response,
                search_queries=[response]
            )


query_agent = QueryAgent(llm=None)
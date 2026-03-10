from typing import TypedDict


class AgentState(TypedDict):

    #用户输入
    query: str
    #重写输入
    rewritten_query: str
    #检索到的document
    retrieved_docs: list
    #重新排序的document
    reranked_docs: list
    #回答
    answer: str
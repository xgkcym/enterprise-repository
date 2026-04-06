
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from core.settings import settings


class WebSearchContext(BaseModel):
    query: Optional[str] = Field(default="", description="原始查询")
    rewritten_query: Optional[str] = Field(default="", description="重写后的查询")
    expand_query: List[str] = Field(default_factory=list, description="扩展后的查询列表")
    decompose_query: List[str] = Field(default_factory=list, description="分解后的子查询列表")
    retrieval_top_k: int = Field(default=settings.retriever_top_k, description="搜索结果数量")
    rerank_top_k: int = Field(default=settings.reranker_top_k, description="为保持协议一致保留的字段")
    use_retrieval: bool = Field(default=True, description="是否重新执行搜索")
    use_rerank: bool = Field(default=False, description="Web 搜索默认不做本地重排")
    search_engine: Literal[
        "search_std",
        "search_pro",
        "search_pro_sogou",
        "search_pro_quark",
    ] = Field(default="search_std", description="智谱 Web Search 搜索引擎")
    count: int = Field(default=5, description="每次搜索返回结果条数")





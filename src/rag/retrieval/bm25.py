import jieba
from rank_bm25 import BM25Okapi

from core.settings import settings
from utils.utils import is_chinese




class BM25Retriever:
    @staticmethod
    def create(mode = settings.bm5_retrieval_mode):
        if mode == "lite":
            return BM25LiteRetriever()
        elif mode == "es":
            return ESRetriever()
        else:
            raise Exception("retrieval type error")


class BaseBM25Retrieval:
    def run(self,search_queries: list[str], top_k=settings.retriever_top_k, filters=None):
        raise NotImplementedError


class BM25LiteRetriever(BaseBM25Retrieval):

    def __init__(self, documents=None):
        self.docs = documents
        self.en_corpus = [doc["content"].split() for doc in documents]
        self.zh_corpus = [jieba.lcut(doc["content"]) for doc in documents]
        self.en_bm25 = BM25Okapi(self.en_corpus)
        self.zh_bm25 = BM25Okapi(self.zh_corpus)

    def run(self, search_queries: list[str], top_k=settings.retriever_top_k,filters=None):
        results = []
        for query in search_queries:
            if is_chinese(query):
                tokenized_query = jieba.lcut(query)
                scores = self.zh_bm25.get_scores(tokenized_query)
            else:
                tokenized_query = query.split()
                scores = self.en_bm25.get_scores(tokenized_query)

            for doc, score in zip(self.docs, scores):
                results.append({
                    "content": doc["content"],
                    "metadata": doc.get("metadata", {}),
                    "bm25_score": float(score)
                })
        results.sort(key=lambda x: x["bm25_score"], reverse=True)
        return results[:top_k]




class ESRetriever(BaseBM25Retrieval):

    def __init__(self, es_client = None, index_name="rag_docs"):
        self.es = es_client
        self.index = index_name

    def run(self, search_queries: list[str], top_k=20, filters=None):

        must = [{"match": {"content": query}} for query in search_queries]

        filter_clause = []

        if filters:
            for k, v in filters.items():
                filter_clause.append({
                    "term": {k: v}
                })

        body = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": must,
                    "filter": filter_clause
                }
            }
        }

        res = self.es.search(index=self.index, body=body)

        results = []
        for hit in res["hits"]["hits"]:
            results.append({
                "content": hit["_source"]["content"],
                "metadata": hit["_source"],
                "bm25_score": hit["_score"]
            })

        return results
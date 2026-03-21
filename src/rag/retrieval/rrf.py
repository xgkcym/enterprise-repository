from core.settings import settings


def rrf_fusion(results_list, k=settings.retriever_top_k):
    """
    results_list: List[List[docs]]
    """

    scores = {}

    for results in results_list:
        for rank, doc in enumerate(results):
            doc_id = doc["content"]  # 或hash

            if doc_id not in scores:
                scores[doc_id] = 0

            scores[doc_id] += 1 / (k + rank)

    # 合并文档
    merged = {}

    for results in results_list:
        for doc in results:
            doc_id = doc["content"]
            merged[doc_id] = doc

    # 排序
    sorted_docs = sorted(
        merged.values(),
        key=lambda d: scores[d["content"]],
        reverse=True
    )

    return sorted_docs
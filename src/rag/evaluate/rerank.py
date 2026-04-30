from core.settings import settings
from tqdm import tqdm

from src.rag.evaluate.function import recall_at_k, mrr_multi, coverage


def evaluate_rerank(retrieval, reranker, benchmark, top_k=settings.reranker_top_k):
    total_recall = 0
    total_mrr = 0
    total_coverage = 0

    for item in tqdm(benchmark, desc="重排评估中..."):
        question = item.get("question") or ""
        if not question:
            continue

        retrieval_data = retrieval.run([question])
        docs = reranker.run(question, docs=retrieval_data, top_k=top_k)
        if not docs:
            continue

        gt = item["node_ids"]

        # 召回率@K
        recall = recall_at_k(docs, gt)
        total_recall += recall

        # 平均倒数排名
        mrr = mrr_multi(docs, gt)
        total_mrr += mrr

        # 覆盖率
        cov = coverage(docs, gt)
        total_coverage += cov

    n = len(benchmark)

    return {
        "recall@k": total_recall / n,
        "mrr": total_mrr / n,
        "coverage": total_coverage / n,
    }

from src.rag.rag_service import rag_service
from src.types.rag_type import RagContext
from src.types.rag_type import RAGResult, DocumentInfo
from src.rag.evaluate.function import recall_at_k, coverage as cov_func
from typing import List, Literal

# 阈值配置，可根据实际业务调整
DENSE_SCORE_THRESHOLD = 0.3
RERANK_SCORE_THRESHOLD = 0.5
CONFIDENCE_WEIGHT = {"dense": 0.4, "bm25": 0.3, "rerank": 0.3}

def compute_confidence(rag_result: RAGResult) -> float:
    """计算 confidence，基于 top 文档分数加权"""
    if not rag_result.documents:
        return 0.0
    scores = []
    for doc in rag_result.documents:
        dense = doc.dense_score or 0.0
        bm25 = doc.bm25_score or 0.0
        rerank = doc.rerank_score or 0.0
        score = (dense * CONFIDENCE_WEIGHT["dense"] +
                 bm25 * CONFIDENCE_WEIGHT["bm25"] +
                 rerank * CONFIDENCE_WEIGHT["rerank"])
        scores.append(score)
    # 返回 top 3 文档平均 confidence
    top_scores = sorted(scores, reverse=True)[:3]
    return sum(top_scores) / len(top_scores)


def compute_coverage(rag_result: RAGResult, ground_truth_ids: List[str] = None) -> float:
    """计算 coverage，如果提供 ground truth 可做严格计算，否则用 top-K 是否覆盖"""
    if not rag_result.documents:
        return 0.0
    if ground_truth_ids:
        doc_ids = [d.node_id for d in rag_result.documents]
        return int(all(gt in doc_ids for gt in ground_truth_ids))
    else:
        # 没有 ground truth 时，用 top-K 非空判断
        return int(bool(rag_result.documents))


def decide_fail_reason(rag_result: RAGResult) ->  Literal[
        "low_recall",
        "bad_ranking",
        "ambiguous_query",
        "no_data",
    ] :
    """根据文档分数、is_sufficient 判断 fail_reason"""
    if rag_result.is_sufficient:
        return "no_data"
    if all((d.dense_score or 0.0) < DENSE_SCORE_THRESHOLD for d in rag_result.documents):
        return "low_recall"
    elif any((d.rerank_score or 0.0) < RERANK_SCORE_THRESHOLD for d in rag_result.documents):
        return "bad_ranking"
    else:
        return "ambiguous_query"



def rag_tool(query:RagContext,user_context:dict):
    return rag_service.query(query,user_context)
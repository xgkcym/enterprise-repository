from src.rag.evaluate.llm_evaluate_answer import evaluate_answer
from src.rag.context.builder import ContextBuilder
from src.rag.generation.generator import evaluate_evidence


def evaluate_generation(answer_llm, benchmark, retriever, rerank, judge_llm=None):
    total_score = 0
    total_correct = 0
    total_citation_correct = 0
    total_retrieval_coverage = 0
    total_rerank_coverage = 0
    total_retrieval_recall = 0
    total_rerank_recall = 0
    judge = judge_llm or answer_llm

    for item in benchmark:
        question = item.get("question") or ""
        if not question:
            continue

        # 检索
        retrieval_data = retriever.run([question])

        # 重排序
        rerank_data = rerank.run(question, docs=retrieval_data)

        if not rerank_data:
            continue

        retrieval_ids = [d["node_id"] for d in retrieval_data]
        rerank_ids = [d["node_id"] for d in rerank_data]

        # 基于当前重排序结果生成证据摘要
        context = ContextBuilder().run(rerank_data)
        response = evaluate_evidence(answer_llm, question, context)
        answer_text = response.evidence_summary or ""
        answer_citations = list(response.citations or [])

        #  LLM评估答案
        score = evaluate_answer(
            judge,
            question,
            item.get("answer") or "",
            answer_text,
        )

        total_score += score

        if score >= 0.8:
            total_correct += 1

        gt_ids = item["node_ids"]

        # 引用覆盖率
        retrieval_coverage = int(all(gt in retrieval_ids for gt in gt_ids))
        total_retrieval_coverage += retrieval_coverage

        rerank_coverage = int(all(gt in rerank_ids for gt in gt_ids))
        total_rerank_coverage += rerank_coverage

        # 检索召回率
        total_retrieval_recall += sum(1 for gt in gt_ids if gt in retrieval_ids) / len(gt_ids)

        # 重排序召回率
        total_rerank_recall += sum(1 for gt in gt_ids if gt in rerank_ids) / len(gt_ids)

        # 引用正确性
        citation_coverage = int(all(gt in answer_citations for gt in gt_ids))
        total_citation_correct += citation_coverage

    n = len(benchmark)

    return {
        # LLM 答案理解是否正确
        "answer_accuracy": total_correct / n,
        "avg_score": total_score / n,
        # 是否引用了正确来源（防幻觉）
        "citation_accuracy": total_citation_correct / n,
        # 检索是否提供足够信息
        "retrieval_coverage": total_retrieval_coverage / n,

        "retrieval_recall": total_retrieval_recall / n,
        "rerank_recall": total_rerank_recall / n,
        # 重排序是否提供足够信息
        "rerank_coverage": total_rerank_coverage / n,
    }

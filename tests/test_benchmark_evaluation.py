import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.rag.evaluate.generation import evaluate_generation
from src.rag.evaluate.rerank import evaluate_rerank


class FakeRetriever:
    def __init__(self, docs):
        self.docs = [dict(doc) for doc in docs]
        self.calls = []

    def run(self, search_queries, **kwargs):
        self.calls.append(search_queries)
        return [dict(doc) for doc in self.docs]


class FakeReranker:
    def __init__(self, docs):
        self.docs = [dict(doc) for doc in docs]
        self.calls = []

    def run(self, query, docs, top_k=None, **kwargs):
        self.calls.append({"query": query, "docs": [dict(doc) for doc in docs], "top_k": top_k})
        return [dict(doc) for doc in self.docs]


class BenchmarkEvaluationTests(unittest.TestCase):
    def test_evaluate_rerank_uses_full_question_list_for_retrieval(self):
        docs = [
            {"node_id": "node-1", "content": "营业收入为100万元", "rerank_score": 0.95},
            {"node_id": "node-2", "content": "净利润为10万元", "rerank_score": 0.90},
        ]
        retriever = FakeRetriever(docs)
        reranker = FakeReranker(docs)
        benchmark = [
            {
                "question": "营业收入和净利润分别是多少？",
                "node_ids": ["node-1", "node-2"],
            }
        ]

        report = evaluate_rerank(retriever, reranker, benchmark, top_k=3)

        self.assertEqual(retriever.calls, [["营业收入和净利润分别是多少？"]])
        self.assertEqual(reranker.calls[0]["query"], "营业收入和净利润分别是多少？")
        self.assertEqual(report["recall@k"], 1.0)
        self.assertEqual(report["mrr"], 0.75)
        self.assertEqual(report["coverage"], 1.0)

    def test_evaluate_generation_uses_evidence_summary_and_separate_judge_llm(self):
        docs = [
            {"node_id": "node-1", "content": "营业收入为100万元", "rerank_score": 0.95},
            {"node_id": "node-2", "content": "净利润为10万元", "rerank_score": 0.90},
        ]
        retriever = FakeRetriever(docs)
        reranker = FakeReranker(docs)
        benchmark = [
            {
                "question": "营业收入和净利润分别是多少？",
                "answer": "营业收入100万元，净利润10万元。",
                "node_ids": ["node-1", "node-2"],
            }
        ]
        generated = SimpleNamespace(
            evidence_summary="营业收入100万元，净利润10万元。",
            citations=["node-1", "node-2"],
        )

        with (
            patch("src.rag.evaluate.generation.evaluate_evidence", return_value=generated) as evidence_mock,
            patch("src.rag.evaluate.generation.evaluate_answer", return_value=0.92) as answer_mock,
        ):
            report = evaluate_generation(
                answer_llm="answer-llm",
                judge_llm="judge-llm",
                benchmark=benchmark,
                retriever=retriever,
                rerank=reranker,
            )

        self.assertEqual(retriever.calls, [["营业收入和净利润分别是多少？"]])
        self.assertEqual(evidence_mock.call_args.args[0], "answer-llm")
        self.assertEqual(evidence_mock.call_args.args[1], "营业收入和净利润分别是多少？")
        self.assertIn("[node_id:node-1]", evidence_mock.call_args.args[2])
        self.assertIn("[node_id:node-2]", evidence_mock.call_args.args[2])
        self.assertEqual(answer_mock.call_args.args[0], "judge-llm")
        self.assertEqual(answer_mock.call_args.args[3], "营业收入100万元，净利润10万元。")
        self.assertEqual(report["answer_accuracy"], 1.0)
        self.assertEqual(report["avg_score"], 0.92)
        self.assertEqual(report["citation_accuracy"], 1.0)
        self.assertEqual(report["retrieval_coverage"], 1.0)
        self.assertEqual(report["retrieval_recall"], 1.0)
        self.assertEqual(report["rerank_recall"], 1.0)
        self.assertEqual(report["rerank_coverage"], 1.0)


if __name__ == "__main__":
    unittest.main()

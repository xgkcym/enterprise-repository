import os
import unittest
from unittest.mock import patch

_TEST_ENV = {
    "DELETE_FILE": "false",
    "DATABASE_NAME": "test_db",
    "DATABASE_STRING": "postgresql://user:pass@localhost:5432/test_db",
    "DATABASE_ASYNC_STRING": "postgresql+asyncpg://user:pass@localhost:5432/test_db",
    "VECTOR_TABLE_NAME": "vectors",
    "EMBEDDING_MODEL": "text-embedding-3-small",
    "EMBEDDING_DIM": "1536",
    "MONGODB_URL": "mongodb://localhost:27017",
    "MONGODB_DB_NAME": "test_db",
    "DOC_COLLECTION_NAME": "docs",
    "QA_COLLECTION_NAME": "qa",
    "ELASTICSEARCH_URL": "http://localhost:9200",
    "METADATA_VERSION": "1",
    "TXT_CHUNK_SIZE": "500",
    "TXT_CHUNK_OVERLAP": "50",
    "TXT_MIN_CHUNK_SIZE": "100",
    "DOCX_CHUNK_SIZE": "500",
    "DOCX_CHUNK_OVERLAP": "50",
    "DOCX_MIN_CHUNK_SIZE": "100",
    "MD_CHUNK_SIZE": "500",
    "MD_CHUNK_OVERLAP": "50",
    "MD_MIN_CHUNK_SIZE": "100",
    "PDF_CHUNK_SIZE": "500",
    "PDF_CHUNK_OVERLAP": "50",
    "OCR_LANG": "ch",
    "OCR_MIN_SCORE": "0.5",
    "EXCEL_CHUNK_SIZE": "500",
    "EXCEL_MIN_CHUNK_SIZE": "100",
    "EXCEL_CHUNK_OVERLAP": "50",
    "EXCEL_HEADER_MODE": "multi",
    "PPTX_CHUNK_SIZE": "500",
    "PPTX_CHUNK_OVERLAP": "50",
    "JSON_CHUNK_SIZE": "500",
    "JSON_CHUNK_OVERLAP": "50",
    "JSON_MIN_CHUNK_SIZE": "100",
    "IMAGE_CHUNK_SIZE": "500",
    "IMAGE_CHUNK_OVERLAP": "50",
    "RETRIEVER_TOP_K": "5",
    "RERANKER_TOP_K": "5",
    "RERANKER_TYPE": "llm",
    "BM25_RETRIEVAL_MODE": "lite",
    "RERANKER_MAX_LEN": "512",
    "RETRIEVAL_MIN_SCORE": "0.1",
    "RERANKER_MIN_SCORE": "0.1",
    "CONTEXT_MAX_LEN": "4000",
    "MAX_EXPAND": "3",
    "UPDATE_DOC_TIME": "60",
    "MAX_RETRIES": "1",
    "MAX_TIMEOUT": "30",
    "HF_TOKEN": "test-token",
    "RERANKER_MODEL": "test-reranker",
    "OPENAI_API_KEY": "test-openai-key",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_BASE_URL": "https://api.openai.com/v1",
    "DEEPSEEK_URL": "https://api.deepseek.com",
    "DEEPSEEK_MODEL": "deepseek-chat",
    "DEEPSEEK_API_KEY": "test-deepseek-key",
    "ZHIPUAI_API_KEY": "test-zhipu-key",
}

for _key, _value in _TEST_ENV.items():
    os.environ.setdefault(_key, _value)

from src.agent.profile_utils import (
    build_topic_guidance_queries,
    extract_preferred_topics,
    merge_queries_with_topic_guidance,
)
from src.agent.runner import build_run_report
from src.tools.expand_query_tool import ExpandResult, expand_query_tool
from src.tools.resolved_query_tool import resolved_query_tool
from src.tools.rewrite_query_tool import RewriteResult, rewrite_query_tool
from src.types.agent_state import State
from src.types.event_type import ReasoningEvent, ToolEvent
from src.types.rag_type import RAGResult


class PreferredTopicsProfileUtilsTests(unittest.TestCase):
    def test_extract_preferred_topics_dedupes_case_insensitively_and_limits(self):
        profile = {
            "preferred_topics": [
                "Energy Transition",
                "energy transition",
                " Risk Management ",
                "",
                "Supply Chain",
                "ESG",
                "Forecasting",
                "Extra Topic",
            ]
        }

        result = extract_preferred_topics(profile)

        self.assertEqual(
            result,
            ["Energy Transition", "Risk Management", "Supply Chain", "ESG", "Forecasting"],
        )

    def test_build_topic_guidance_queries_skips_existing_topic_and_limits_results(self):
        result = build_topic_guidance_queries(
            "energy transition strategy",
            {"preferred_topics": ["Energy Transition", "Risk", "Finance", "Compliance"]},
            max_queries=2,
        )

        self.assertEqual(
            result,
            [
                "energy transition strategy Risk",
                "energy transition strategy Finance",
            ],
        )

    def test_merge_queries_with_topic_guidance_preserves_existing_queries(self):
        result = merge_queries_with_topic_guidance(
            ["capital structure analysis", "capital structure analysis"],
            "capital structure",
            {"preferred_topics": ["Energy Transition", "Risk"]},
            limit=3,
            max_topic_queries=1,
        )

        self.assertEqual(
            result,
            [
                "capital structure analysis",
                "capital structure Energy Transition",
            ],
        )


class PreferredTopicsToolIntegrationTests(unittest.TestCase):
    def test_rewrite_query_tool_includes_preferred_topics_note_and_marks_diagnostic(self):
        def fake_invoke(*, llm, messages, schema, fallback_llm=None):
            self.assertIn("preferred_topics", messages[0].content)
            self.assertIn("Energy Transition", messages[0].content)
            return RewriteResult(answer="rewritten question", success=True, diagnostics=[])

        with patch("src.tools.rewrite_query_tool.LLMService.invoke", side_effect=fake_invoke):
            result = rewrite_query_tool(
                llm=object(),
                query="What should we focus on?",
                chat_history=["user: summarize the latest board discussion"],
                user_profile={"preferred_topics": ["Energy Transition"]},
            )

        self.assertTrue(result.success)
        self.assertEqual(result.answer, "rewritten question")
        self.assertIn("preferred_topics_hint_applied:rewrite_query", result.diagnostics)

    def test_expand_query_tool_adds_topic_guidance_variant(self):
        def fake_invoke(*, llm, messages, schema, fallback_llm=None):
            self.assertIn("preferred_topics", messages[0].content)
            return ExpandResult(answer=["capital structure analysis"], success=True, diagnostics=[])

        with patch("src.tools.expand_query_tool.LLMService.invoke", side_effect=fake_invoke):
            result = expand_query_tool(
                llm=object(),
                query="capital structure",
                chat_history=[],
                user_profile={"preferred_topics": ["Energy Transition"]},
            )

        self.assertTrue(result.success)
        self.assertIn("capital structure analysis", result.answer)
        self.assertIn("capital structure Energy Transition", result.answer)
        self.assertIn("preferred_topics_hint_applied:expand_query", result.diagnostics)

    def test_resolved_query_tool_records_topic_hint_availability_without_history(self):
        result = resolved_query_tool(
            llm=object(),
            query="How about this one?",
            chat_history=[],
            user_profile={"preferred_topics": ["Risk"]},
        )

        self.assertTrue(result.success)
        self.assertIn("resolved_query_no_history", result.diagnostics)
        self.assertIn("preferred_topics_hint_available:resolved_query", result.diagnostics)


class PreferredTopicsRunReportTests(unittest.TestCase):
    def test_build_run_report_summarizes_preferred_topics_usage(self):
        rewrite_event = ReasoningEvent(
            name="rewrite_query",
            status="success",
            output=RewriteResult(
                success=True,
                answer="rewritten",
                diagnostics=["preferred_topics_hint_applied:rewrite_query"],
            ),
        )
        rag_event = ToolEvent(
            name="rag",
            status="success",
            output=RAGResult(
                success=True,
                answer="final answer",
                diagnostics=[
                    "preferred_topics_available=2",
                    "preferred_topic_guidance_queries=1",
                ],
            ),
        )

        state = State(
            query="What changed this quarter?",
            user_profile={"preferred_topics": ["Energy Transition", "Risk"]},
            action_history=[rewrite_event, rag_event],
            answer="final answer",
            status="success",
        )

        report = build_run_report(state)
        usage = report["preferred_topics_usage"]

        self.assertEqual(usage["available_topics"], ["Energy Transition", "Risk"])
        self.assertTrue(usage["used"])
        self.assertEqual(usage["applied_steps"], ["rewrite_query", "rag"])
        self.assertEqual(usage["guidance_query_count"], 1)
        self.assertIn("preferred_topics_hint_applied:rewrite_query", usage["matched_diagnostics"])


if __name__ == "__main__":
    unittest.main()

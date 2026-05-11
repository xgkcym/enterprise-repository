import unittest

from core.settings import Settings


class RuntimeConfigTests(unittest.TestCase):
    def test_validate_runtime_config_reports_missing_core_settings(self):
        settings = Settings(
            database_string="",
            database_async_string="",
            mongodb_url="",
            mongodb_db_name="",
            vector_table_name="",
            embedding_model="",
            doc_collection_name="",
            qa_collection_name="",
            openai_model="",
            openai_base_url="",
            deepseek_model="",
            deepseek_base_url="",
            cors_allow_origins=["http://localhost:5173"],
            cors_allow_methods=["GET"],
            cors_allow_headers=["Authorization"],
        )

        with self.assertRaises(RuntimeError) as exc:
            settings.validate_runtime_config()

        message = str(exc.exception)
        self.assertIn("DATABASE_ASYNC_STRING", message)
        self.assertIn("DATABASE_STRING", message)
        self.assertIn("MONGODB_URL", message)
        self.assertIn("VECTOR_TABLE_NAME", message)
        self.assertIn("EMBEDDING_MODEL", message)
        self.assertIn("DOC_COLLECTION_NAME", message)
        self.assertIn("QA_COLLECTION_NAME", message)


if __name__ == "__main__":
    unittest.main()

import logging
import os
import pathlib
from typing import Literal

import dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

dotenv.load_dotenv()
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

_DEV_ONLY_JWT_SECRET = "dev-only-jwt-secret-change-me"
_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off", ""}


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return float(value)


def _env_csv(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None or not value.strip():
        return list(default)

    if value.strip() == "*":
        return ["*"]

    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or list(default)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", arbitrary_types_allowed=True)

    root_dir: pathlib.Path = Field(default=pathlib.Path(__file__).resolve().parent.parent)

    app_env: Literal["development", "staging", "production"] = Field(default=os.getenv("APP_ENV", "development"))
    debug: bool = Field(default=_env_bool("DEBUG", False))
    server_host: str = Field(default=os.getenv("SERVER_HOST", "127.0.0.1"))
    server_port: int = Field(default=_env_int("SERVER_PORT", 1016))
    database_auto_create: bool = Field(default=_env_bool("DATABASE_AUTO_CREATE", False))
    serve_public_files: bool = Field(default=_env_bool("SERVE_PUBLIC_FILES", False))
    public_dir: str | None = Field(default=os.getenv("PUBLIC_DIR"))
    public_url_path: str = Field(default=os.getenv("PUBLIC_URL_PATH", "/public"))
    upload_max_size_mb: int = Field(default=_env_int("UPLOAD_MAX_SIZE_MB", 50))
    upload_allowed_extensions: list[str] = Field(
        default=_env_csv(
            "UPLOAD_ALLOWED_EXTENSIONS",
            ["txt", "docx", "md", "pdf", "xlsx", "csv", "pptx", "json", "png", "jpg", "jpeg", "bmp", "gif"],
        )
    )

    jwt_secret_key: str = Field(default=os.getenv("JWT_SECRET_KEY", ""))
    jwt_algorithm: str = Field(default=os.getenv("JWT_ALGORITHM", "HS256"))
    access_token_expire_minutes: int = Field(default=_env_int("ACCESS_TOKEN_EXPIRE_MINUTES", 30 * 60))

    cors_allow_origins: list[str] = Field(
        default=_env_csv("CORS_ALLOW_ORIGINS", ["http://localhost:5173", "http://127.0.0.1:5173"])
    )
    cors_allow_methods: list[str] = Field(
        default=_env_csv("CORS_ALLOW_METHODS", ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    )
    cors_allow_headers: list[str] = Field(
        default=_env_csv("CORS_ALLOW_HEADERS", ["Authorization", "Content-Type", "Accept"])
    )

    delete_file: bool = Field(default=_env_bool("DELETE_FILE", False))

    database_name: str | None = Field(default=os.getenv("DATABASE_NAME"))
    database_string: str | None = Field(default=os.getenv("DATABASE_STRING"))
    database_async_string: str | None = Field(default=os.getenv("DATABASE_ASYNC_STRING"))
    vector_table_name: str | None = Field(default=os.getenv("VECTOR_TABLE_NAME"))
    embedding_model: str | None = Field(default=os.getenv("EMBEDDING_MODEL"))
    embedding_dim: int = Field(default=_env_int("EMBEDDING_DIM", 1536))
    memory_backend: Literal["disabled", "milvus"] = Field(default=os.getenv("MEMORY_BACKEND", "disabled"))
    memory_enabled: bool = Field(default=_env_bool("MEMORY_ENABLED", False))
    memory_top_k: int = Field(default=_env_int("MEMORY_TOP_K", 3))
    memory_context_limit: int = Field(default=_env_int("MEMORY_CONTEXT_LIMIT", 3))
    memory_recall_min_score: float = Field(default=_env_float("MEMORY_RECALL_MIN_SCORE", 0.35))
    memory_write_enabled: bool = Field(default=_env_bool("MEMORY_WRITE_ENABLED", False))
    memory_write_min_importance: float = Field(default=_env_float("MEMORY_WRITE_MIN_IMPORTANCE", 0.65))
    milvus_uri: str = Field(default=os.getenv("MILVUS_URI", ""))
    milvus_token: str = Field(default=os.getenv("MILVUS_TOKEN", ""))
    milvus_db_name: str = Field(default=os.getenv("MILVUS_DB_NAME", "default"))
    milvus_collection_name: str = Field(default=os.getenv("MILVUS_COLLECTION_NAME", "long_term_memory"))
    milvus_consistency_level: str = Field(default=os.getenv("MILVUS_CONSISTENCY_LEVEL", "Strong"))
    milvus_search_metric: str = Field(default=os.getenv("MILVUS_SEARCH_METRIC", "COSINE"))
    milvus_index_type: str = Field(default=os.getenv("MILVUS_INDEX_TYPE", "AUTOINDEX"))
    milvus_vector_dim: int = Field(default=_env_int("MILVUS_VECTOR_DIM", _env_int("EMBEDDING_DIM", 1536)))

    mongodb_url: str | None = Field(default=os.getenv("MONGODB_URL"))
    mongodb_db_name: str | None = Field(default=os.getenv("MONGODB_DB_NAME"))
    doc_collection_name: str | None = Field(default=os.getenv("DOC_COLLECTION_NAME"))
    qa_collection_name: str | None = Field(default=os.getenv("QA_COLLECTION_NAME"))
    elasticsearch_url: str | None = Field(default=os.getenv("ELASTICSEARCH_URL"))

    metadata_version: int | None = Field(default=_env_int("METADATA_VERSION", 0) if os.getenv("METADATA_VERSION") else None)
    txt_chunk_size: int | None = Field(default=_env_int("TXT_CHUNK_SIZE", 0) if os.getenv("TXT_CHUNK_SIZE") else None)
    txt_chunk_overlap: int | None = Field(
        default=_env_int("TXT_CHUNK_OVERLAP", 0) if os.getenv("TXT_CHUNK_OVERLAP") else None
    )
    txt_min_chunk_size: int | None = Field(
        default=_env_int("TXT_MIN_CHUNK_SIZE", 0) if os.getenv("TXT_MIN_CHUNK_SIZE") else None
    )
    docx_chunk_size: int | None = Field(default=_env_int("DOCX_CHUNK_SIZE", 0) if os.getenv("DOCX_CHUNK_SIZE") else None)
    docx_chunk_overlap: int | None = Field(
        default=_env_int("DOCX_CHUNK_OVERLAP", 0) if os.getenv("DOCX_CHUNK_OVERLAP") else None
    )
    docx_min_chunk_size: int | None = Field(
        default=_env_int("DOCX_MIN_CHUNK_SIZE", 0) if os.getenv("DOCX_MIN_CHUNK_SIZE") else None
    )
    md_chunk_size: int | None = Field(default=_env_int("MD_CHUNK_SIZE", 0) if os.getenv("MD_CHUNK_SIZE") else None)
    md_chunk_overlap: int | None = Field(
        default=_env_int("MD_CHUNK_OVERLAP", 0) if os.getenv("MD_CHUNK_OVERLAP") else None
    )
    md_min_chunk_size: int | None = Field(
        default=_env_int("MD_MIN_CHUNK_SIZE", 0) if os.getenv("MD_MIN_CHUNK_SIZE") else None
    )
    pdf_chunk_size: int | None = Field(default=_env_int("PDF_CHUNK_SIZE", 0) if os.getenv("PDF_CHUNK_SIZE") else None)
    pdf_chunk_overlap: int | None = Field(
        default=_env_int("PDF_CHUNK_OVERLAP", 0) if os.getenv("PDF_CHUNK_OVERLAP") else None
    )
    orc_lang: str | None = Field(default=os.getenv("OCR_LANG"))
    orc_min_score: float | None = Field(
        default=_env_float("OCR_MIN_SCORE", 0.0) if os.getenv("OCR_MIN_SCORE") else None
    )
    excel_chunk_size: int | None = Field(
        default=_env_int("EXCEL_CHUNK_SIZE", 0) if os.getenv("EXCEL_CHUNK_SIZE") else None
    )
    excel_min_chunk_size: int | None = Field(
        default=_env_int("EXCEL_MIN_CHUNK_SIZE", 0) if os.getenv("EXCEL_MIN_CHUNK_SIZE") else None
    )
    excel_chunk_overlap: int | None = Field(
        default=_env_int("EXCEL_CHUNK_OVERLAP", 0) if os.getenv("EXCEL_CHUNK_OVERLAP") else None
    )
    excel_header_mode: str | None = Field(default=os.getenv("EXCEL_HEADER_MODE"))
    pptx_chunk_size: int | None = Field(default=_env_int("PPTX_CHUNK_SIZE", 0) if os.getenv("PPTX_CHUNK_SIZE") else None)
    pptx_chunk_overlap: int | None = Field(
        default=_env_int("PPTX_CHUNK_OVERLAP", 0) if os.getenv("PPTX_CHUNK_OVERLAP") else None
    )
    pptx_filter_slider: list[str] = Field(default=["thanks", "致谢", "thank you"])
    json_chunk_size: int | None = Field(default=_env_int("JSON_CHUNK_SIZE", 0) if os.getenv("JSON_CHUNK_SIZE") else None)
    json_chunk_overlap: int | None = Field(
        default=_env_int("JSON_CHUNK_OVERLAP", 0) if os.getenv("JSON_CHUNK_OVERLAP") else None
    )
    json_min_chunk_size: int | None = Field(
        default=_env_int("JSON_MIN_CHUNK_SIZE", 0) if os.getenv("JSON_MIN_CHUNK_SIZE") else None
    )
    image_chunk_size: int | None = Field(
        default=_env_int("IMAGE_CHUNK_SIZE", 0) if os.getenv("IMAGE_CHUNK_SIZE") else None
    )
    image_chunk_overlap: int | None = Field(
        default=_env_int("IMAGE_CHUNK_OVERLAP", 0) if os.getenv("IMAGE_CHUNK_OVERLAP") else None
    )

    retriever_top_k: int | None = Field(default=_env_int("RETRIEVER_TOP_K", 0) if os.getenv("RETRIEVER_TOP_K") else None)
    reranker_top_k: int | None = Field(default=_env_int("RERANKER_TOP_K", 0) if os.getenv("RERANKER_TOP_K") else None)
    reranker_type: Literal["llm", "cross-encoder"] | None = Field(default=os.getenv("RERANKER_TYPE"))
    bm25_retrieval_mode: Literal["lite", "es"] | None = Field(default=os.getenv("BM25_RETRIEVAL_MODE"))
    reranker_max_len: int | None = Field(default=_env_int("RERANKER_MAX_LEN", 0) if os.getenv("RERANKER_MAX_LEN") else None)
    retrieval_min_score: float | None = Field(
        default=_env_float("RETRIEVAL_MIN_SCORE", 0.0) if os.getenv("RETRIEVAL_MIN_SCORE") else None
    )
    reranker_min_score: float | None = Field(
        default=_env_float("RERANKER_MIN_SCORE", 0.0) if os.getenv("RERANKER_MIN_SCORE") else None
    )
    context_max_len: int | None = Field(default=_env_int("CONTEXT_MAX_LEN", 0) if os.getenv("CONTEXT_MAX_LEN") else None)
    max_expand: int | None = Field(default=_env_int("MAX_EXPAND", 0) if os.getenv("MAX_EXPAND") else None)
    agent_max_steps: int = Field(default=_env_int("AGENT_MAX_STEPS", 10))
    agent_chat_history_limit: int = Field(default=_env_int("AGENT_CHAT_HISTORY_LIMIT", 8))
    agent_output_level: Literal["concise", "standard", "detailed"] = Field(
        default=os.getenv("AGENT_OUTPUT_LEVEL", "standard")
    )
    monitor_default_input_cost_per_1m: float = Field(default=_env_float("MONITOR_DEFAULT_INPUT_COST_PER_1M", 0.0))
    monitor_default_output_cost_per_1m: float = Field(default=_env_float("MONITOR_DEFAULT_OUTPUT_COST_PER_1M", 0.0))
    monitor_openai_input_cost_per_1m: float = Field(default=_env_float("MONITOR_OPENAI_INPUT_COST_PER_1M", 2.5))
    monitor_openai_output_cost_per_1m: float = Field(default=_env_float("MONITOR_OPENAI_OUTPUT_COST_PER_1M", 10.0))
    monitor_deepseek_input_cost_per_1m: float = Field(default=_env_float("MONITOR_DEEPSEEK_INPUT_COST_PER_1M", 0.27))
    monitor_deepseek_output_cost_per_1m: float = Field(default=_env_float("MONITOR_DEEPSEEK_OUTPUT_COST_PER_1M", 1.1))
    update_doc_time: int | None = Field(default=_env_int("UPDATE_DOC_TIME", 0) if os.getenv("UPDATE_DOC_TIME") else None)
    is_need_doc: bool = Field(default=False)
    await_upload_file_num: int = Field(default=0)

    log_dir: pathlib.Path = Field(default=pathlib.Path(__file__).resolve().parent.parent / "logs")
    log_format: logging.Formatter = Field(
        default=logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    max_retries: int | None = Field(default=_env_int("MAX_RETRIES", 0) if os.getenv("MAX_RETRIES") else None)
    max_timeout: int | None = Field(default=_env_int("MAX_TIMEOUT", 0) if os.getenv("MAX_TIMEOUT") else None)
    hf_token: str | None = Field(default=os.getenv("HF_TOKEN"))
    reranker_model: str | None = Field(default=os.getenv("RERANKER_MODEL"))
    openai_api_key: str | None = Field(default=os.getenv("OPENAI_API_KEY"))
    openai_model: str | None = Field(default=os.getenv("OPENAI_MODEL"))
    openai_base_url: str | None = Field(default=os.getenv("OPENAI_BASE_URL"))
    deepseek_base_url: str | None = Field(default=os.getenv("DEEPSEEK_URL"))
    deepseek_model: str | None = Field(default=os.getenv("DEEPSEEK_MODEL"))
    deepseek_api_key: str | None = Field(default=os.getenv("DEEPSEEK_API_KEY"))
    zhipuai_api_key: str | None = Field(default=os.getenv("ZHIPUAI_API_KEY"))

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def effective_jwt_secret_key(self) -> str:
        if self.jwt_secret_key:
            return self.jwt_secret_key
        return _DEV_ONLY_JWT_SECRET

    @property
    def uses_dev_jwt_secret(self) -> bool:
        return not bool(self.jwt_secret_key)

    @property
    def cors_allow_credentials(self) -> bool:
        return "*" not in self.cors_allow_origins

    @property
    def resolved_public_dir(self) -> pathlib.Path:
        if self.public_dir:
            return pathlib.Path(self.public_dir)
        return self.root_dir / "service" / "public"

    @property
    def normalized_public_url_path(self) -> str:
        if not self.public_url_path:
            return "/public"
        return self.public_url_path if self.public_url_path.startswith("/") else f"/{self.public_url_path}"

    def validate_runtime_config(self) -> None:
        errors: list[str] = []

        if not self.cors_allow_origins:
            errors.append("CORS_ALLOW_ORIGINS cannot be empty.")
        if not self.cors_allow_methods:
            errors.append("CORS_ALLOW_METHODS cannot be empty.")
        if not self.cors_allow_headers:
            errors.append("CORS_ALLOW_HEADERS cannot be empty.")

        if self.is_production:
            if not self.jwt_secret_key:
                errors.append("JWT_SECRET_KEY must be set when APP_ENV=production.")
            if "*" in self.cors_allow_origins:
                errors.append("CORS_ALLOW_ORIGINS cannot contain '*' when APP_ENV=production.")
            if self.serve_public_files:
                errors.append("SERVE_PUBLIC_FILES must be disabled when APP_ENV=production.")

        if errors:
            raise RuntimeError("Invalid runtime configuration:\n- " + "\n- ".join(errors))


settings = Settings()


if __name__ == "__main__":
    print("***" * 50)
    print(settings.delete_file)

from llama_index.core.schema import Document

from core.custom_types import DocumentMetadata
from models.embedding import embed_model
from models.llm import deepseek_llm
from rag.ingestion.chunker import chunk_text
from utils.logger_handler import logger
from llama_index.core import VectorStoreIndex, ServiceContext, Settings

from rag.index.vector_store import vector_store

class RAGService:
    def __init__(self):
        Settings.embed_model = embed_model
        Settings.llm = deepseek_llm

    def pipeline(self, content, metadata: DocumentMetadata):
        """
        数据向量存储
        :param content: 文件内容
        :param metadata: 存储检索
        :return:
        """
        if not content:
            return True

        doc = Document(
            text=content,
            metadata=metadata.dict()
        )
        try:
            nodes = None
            if metadata.file_type == 'txt':
                nodes = chunk_text(doc)

            index = VectorStoreIndex(
                nodes=nodes,
                vector_store=vector_store
            )
            query_engine = index.as_query_engine()

            response = query_engine.query("日常通勤选择穿什么衣服?")

            print(response)

            logger.info(f"[rag向量存储成功]:存储文件:${metadata.file_path}")
            return True
        except Exception as e:
            logger.error(f"[rag向量存储失败]:存储文件:${metadata.file_path}---错误信息:${str(e)}")
            raise Exception("")


rag_service = RAGService()


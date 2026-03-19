import time

import os

from core.custom_types import DocumentMetadata
from src.models.embedding import embed_model
from src.models.llm import deepseek_llm
from utils.logger_handler import logger
from llama_index.core import VectorStoreIndex, Settings, StorageContext
from src.rag.ingestion.loader import  load_file
from src.rag.store.vector_store import vector_store
from src.rag.ingestion.chunker import chunk_file


class RAGService:
    def __init__(self):
        Settings.embed_model = embed_model
        Settings.llm = deepseek_llm

    def ingestion(self, path:str, metadata: DocumentMetadata):
        """
        对文件路径的单个文件进行数据向量存储
        :param path: 文件路径
        :param metadata: 存储检索
        :return:
        """
        if not path or os.path.isdir(path):
            return False
        try:
            start_time = time.time()
            docs = load_file(path, metadata)
            if not docs or len(docs) == 0:
                logger.info(f"[rag向量存储失败]:内容为空")
                return False
            nodes = chunk_file(docs)

            storage_context = StorageContext.from_defaults(
                vector_store=vector_store,
            )

            VectorStoreIndex(
                nodes=nodes,
                storage_context=storage_context,
                embed_model=embed_model,
                show_progress=True,
            )
            elapsed_time = time.time() - start_time
            logger.info(f"[rag向量存储成功]:存储文件:${metadata.file_path} 用时:${elapsed_time}s")
            return True
        except Exception as e:
            logger.error(f"[rag向量存储失败]:存储文件:${metadata.file_path}---错误信息:${str(e)}")
            raise Exception(f"[rag向量存储失败]:存储文件:${metadata.file_path}---错误信息:${str(e)}") from e



    def query(self,query:str,user_context:dict):
        pass


rag_service = RAGService()

if  __name__ == "__main__":
    data = DocumentMetadata(
         department_id=1,
         department_name="TQ",
         user_id=1,
         user_name="EdenXie",
         file_path="public\\uploads\\TQ\\文档上传测试.pdf",
         file_name= "文档上传测试.pdf",
         file_size=100,
         file_type="pdf",
         source="pdf"
     )
    rag_service.ingestion("D:\\python\\agent_project\\rag-agent\\service\\public\\uploads\\TQ\\文档上传测试.pdf",data)

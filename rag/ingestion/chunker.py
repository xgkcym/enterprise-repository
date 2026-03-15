from langchain_core.documents import Document
from llama_index.core.node_parser import SentenceSplitter

from core.settings import settings


def chunk_text(doc: Document):
    """
    将文本切成 nodes
    """
    splitter = SentenceSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )
    nodes = splitter.get_nodes_from_documents([doc])
    return nodes
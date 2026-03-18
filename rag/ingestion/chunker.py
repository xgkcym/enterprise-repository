from typing import Sequence

from langchain_core.documents import Document
from llama_index.core.node_parser import SentenceSplitter
from utils.logger_handler import logger
from core.settings import settings

def chunk_txt(doc: Sequence[Document]):
    """
    将文本切成 nodes
    """
    splitter = SentenceSplitter(
        chunk_size=settings.txt_chunk_size,
        chunk_overlap=settings.txt_chunk_overlap
    )
    nodes = splitter.get_nodes_from_documents(doc)
    return nodes

def chunk_docx(doc: Sequence[Document]):
    """
   将docx文档切成 nodes 优先保持页和标题语义完整
   """
    nodes = []
    for d in doc:
        # 如果文本长度小于 chunk_size，直接作为 node
        if len(d.text) <= settings.docx_chunk_size:
            nodes.append(d)
        else:
            # 长文本再用 SentenceSplitter 切
            splitter = SentenceSplitter(
                chunk_size=settings.docx_chunk_size,
                chunk_overlap=settings.docx_chunk_overlap
            )
            nodes.extend(splitter.get_nodes_from_documents([d]))
    return nodes



def chunk_markdown(doc: Sequence[Document]):
    """
    将markdown切成 nodes 优先保持页和标题语义完整
    """
    nodes = []
    # 长文本再用 SentenceSplitter 切
    splitter = SentenceSplitter(
        chunk_size=settings.md_chunk_size,
        chunk_overlap=settings.md_chunk_overlap
    )
    for d in doc:
        # 如果文本长度小于 chunk_size，直接作为 node
        if len(d.text) <= settings.md_chunk_size:
            nodes.append(d)
        else:
            nodes.extend(splitter.get_nodes_from_documents([d]))
    return nodes


def chunk_pdf(doc: Sequence[Document]):
    """
        将pdf切成 nodes，优先保持页和标题语义完整
        """
    nodes = []
    # 长文本再用 SentenceSplitter 切
    splitter = SentenceSplitter(
        chunk_size=settings.pdf_chunk_size,
        chunk_overlap=settings.pdf_chunk_overlap
    )
    for d in doc:
        # 如果文本长度小于 chunk_size，直接作为 node
        if len(d.text) <= settings.pdf_chunk_size:
            nodes.append(d)
        else:
            nodes.extend(splitter.get_nodes_from_documents([d]))
    return nodes


def chunk_excel(documents: Sequence[Document]):
    """
    针对 Excel 的最优 chunk：
    - 默认每行一条 node
    - 长行文本再用 SentenceSplitter 细分
    """
    splitter = SentenceSplitter(
        chunk_size=settings.excel_chunk_size,
        chunk_overlap=settings.excel_chunk_overlap
    )

    nodes = []
    for doc in documents:
        text = doc.text.strip()
        # 如果一行文本很长，切成多个 node
        if len(text) > settings.excel_chunk_size:
            nodes.extend(splitter.get_nodes_from_documents([doc]))
        else:
            nodes.append(doc)

    return nodes

def chunk_pptx(doc: Sequence[Document]):
    """
    - 默认每行一条 node
    - 长行文本再用 SentenceSplitter 细分
    """
    splitter = SentenceSplitter(
        chunk_size=settings.pdf_chunk_size,
        chunk_overlap=settings.pdf_chunk_overlap
    )

    nodes = []
    for d in doc:
        # 如果文本长度小于 chunk_size，直接作为 node
        if len(d.text) <= settings.pdf_chunk_size:
            nodes.append(d)
        else:
            nodes.extend(splitter.get_nodes_from_documents([d]))
    return nodes


def chunk_json(doc: Sequence[Document]):
    """
    将json切成 nodes
    """
    splitter = SentenceSplitter(
        chunk_size=settings.json_chunk_size,
        chunk_overlap=settings.json_chunk_overlap
    )
    nodes = []
    for d in doc:
        # 如果文本长度小于 chunk_size，直接作为 node
        if len(d.text) <= settings.json_chunk_size:
            nodes.append(d)
        else:
            nodes.extend(splitter.get_nodes_from_documents([d]))
    return nodes



def chunk_file(doc: Sequence[Document]):
    if doc[0].metadata["file_type"] == "txt":
        return chunk_txt(doc)
    elif doc[0].metadata["file_type"] == "docx" or  doc[0].metadata["file_type"] == "doc":
        return chunk_docx(doc)
    elif doc[0].metadata["file_type"] == "md" or  doc[0].metadata["file_type"] == "markdown":
        return chunk_markdown(doc)
    elif doc[0].metadata["file_type"] == "pdf":
        return chunk_pdf(doc)
    elif doc[0].metadata["file_type"] == "xlsx" or  doc[0].metadata["file_type"] == "xls" or  doc[0].metadata["file_type"] == "csv":
        return chunk_excel(doc)
    elif doc[0].metadata["file_type"] == "pptx" or  doc[0].metadata["file_type"] == "ppt":
        return chunk_pptx(doc)
    elif doc[0].metadata["file_type"] == "json":
        return chunk_json(doc)
    else:
        return chunk_txt(doc)
from typing import List, Sequence

from langchain_core.documents import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode
from llama_index.core.schema import Document as LlamaDocument

from core.settings import settings


def build_chunk_patch(nodes: List[BaseNode], min_chunk_size: int, chunk_size: int = 500):
    if not nodes:
        return []

    chunks = []
    text_list = []
    current_node = None

    def flush_current_chunk():
        nonlocal current_node, text_list
        if not current_node or not text_list:
            return
        chunks.append(
            LlamaDocument(
                text="\n".join(text_list),
                id_=current_node.id_,
                metadata=current_node.metadata.copy(),
            )
        )
        current_node = None
        text_list = []

    for node in nodes:
        if not current_node:
            current_node = node.copy()
        elif current_node.metadata != node.metadata:
            flush_current_chunk()
            current_node = node.copy()

        text_list.append(node.text)

        if len("\n".join(text_list)) >= min_chunk_size:
            flush_current_chunk()

    if text_list:
        if (
            chunks
            and current_node
            and chunks[-1].metadata == current_node.metadata
            and len(chunks[-1].text) + len("\n".join(text_list)) < chunk_size
        ):
            chunks[-1] = LlamaDocument(
                text=chunks[-1].text + "\n\n" + "\n".join(text_list),
                id_=chunks[-1].id_,
                metadata=chunks[-1].metadata.copy(),
            )
        else:
            flush_current_chunk()

    return chunks


def merge_small_pdf_nodes(nodes: Sequence[Document]) -> List[Document]:
    """Merge very small continuation pages back into the previous PDF node."""
    if not nodes:
        return []

    merged: List[Document] = []
    continuation_threshold = max(80, settings.pdf_chunk_size // 5)
    sentence_endings = "。！？.!?;；:"

    for node in nodes:
        text = (node.text or "").strip()
        page = node.metadata.get("page")
        if (
            merged
            and text
            and len(text) <= continuation_threshold
            and not text.startswith("#")
            and isinstance(page, int)
            and isinstance(merged[-1].metadata.get("page"), int)
            and page == merged[-1].metadata["page"] + 1
            and merged[-1].metadata.get("file_path") == node.metadata.get("file_path")
            and (merged[-1].text or "").rstrip()[-1:] not in sentence_endings
        ):
            merged[-1] = LlamaDocument(
                text=merged[-1].text.rstrip() + "\n" + text,
                id_=merged[-1].id_,
                metadata=merged[-1].metadata.copy(),
            )
            continue

        merged.append(node)

    return merged


def chunk_txt(doc: Sequence[Document]):
    splitter = SentenceSplitter(
        chunk_size=settings.txt_chunk_size,
        chunk_overlap=settings.txt_chunk_overlap,
    )
    nodes = splitter.get_nodes_from_documents(doc)
    return build_chunk_patch(nodes, settings.txt_min_chunk_size, settings.txt_chunk_size)


def chunk_docx(doc: Sequence[Document]):
    nodes = []
    for d in doc:
        if len(d.text) <= settings.docx_chunk_size:
            nodes.append(d)
        else:
            splitter = SentenceSplitter(
                chunk_size=settings.docx_chunk_size,
                chunk_overlap=settings.docx_chunk_overlap,
            )
            nodes.extend(splitter.get_nodes_from_documents([d]))
    return build_chunk_patch(nodes, settings.docx_min_chunk_size, settings.docx_chunk_size)


def chunk_markdown(doc: Sequence[Document]):
    nodes = []
    splitter = SentenceSplitter(
        chunk_size=settings.md_chunk_size,
        chunk_overlap=settings.md_chunk_overlap,
    )
    for d in doc:
        if len(d.text) <= settings.md_chunk_size:
            nodes.append(d)
        else:
            nodes.extend(splitter.get_nodes_from_documents([d]))
    return build_chunk_patch(nodes, settings.md_min_chunk_size, settings.md_chunk_size)


def chunk_pdf(doc: Sequence[Document]):
    nodes = []
    splitter = SentenceSplitter(
        chunk_size=settings.pdf_chunk_size,
        chunk_overlap=settings.pdf_chunk_overlap,
    )
    for d in doc:
        if len(d.text) <= settings.pdf_chunk_size:
            nodes.append(d)
        else:
            nodes.extend(splitter.get_nodes_from_documents([d]))
    return merge_small_pdf_nodes(nodes)


def chunk_excel(documents: Sequence[Document]):
    splitter = SentenceSplitter(
        chunk_size=settings.excel_chunk_size,
        chunk_overlap=settings.excel_chunk_overlap,
    )

    nodes = []
    for doc in documents:
        text = doc.text.strip()
        if len(text) > settings.excel_chunk_size:
            nodes.extend(splitter.get_nodes_from_documents([doc]))
        else:
            nodes.append(doc)
    return nodes


def chunk_pptx(doc: Sequence[Document]):
    splitter = SentenceSplitter(
        chunk_size=settings.pptx_chunk_size,
        chunk_overlap=settings.pptx_chunk_overlap,
    )

    nodes = []
    for d in doc:
        if len(d.text) <= settings.pptx_chunk_size:
            nodes.append(d)
        else:
            nodes.extend(splitter.get_nodes_from_documents([d]))
    return nodes


def chunk_json(doc: Sequence[Document]):
    splitter = SentenceSplitter(
        chunk_size=settings.json_chunk_size,
        chunk_overlap=settings.json_chunk_overlap,
    )
    nodes = []
    for d in doc:
        if len(d.text) <= settings.json_chunk_size:
            nodes.append(d)
        else:
            nodes.extend(splitter.get_nodes_from_documents([d]))
    return nodes


def chunk_image(doc: Sequence[Document]):
    splitter = SentenceSplitter(
        chunk_size=settings.image_chunk_size,
        chunk_overlap=settings.image_chunk_overlap,
    )
    nodes = []
    for d in doc:
        if len(d.text) <= settings.image_chunk_size:
            nodes.append(d)
        else:
            nodes.extend(splitter.get_nodes_from_documents([d]))
    return nodes


def chunk_file(doc: Sequence[Document]):
    if doc[0].metadata["file_type"] == "txt":
        return chunk_txt(doc)
    elif doc[0].metadata["file_type"] in ["docx", "doc"]:
        return chunk_docx(doc)
    elif doc[0].metadata["file_type"] in ["md", "markdown"]:
        return chunk_markdown(doc)
    elif doc[0].metadata["file_type"] == "pdf":
        return chunk_pdf(doc)
    elif doc[0].metadata["file_type"] in ["xlsx", "xls", "csv"]:
        return chunk_excel(doc)
    elif doc[0].metadata["file_type"] in ["pptx", "ppt"]:
        return chunk_pptx(doc)
    elif doc[0].metadata["file_type"] == "json":
        return chunk_json(doc)
    elif doc[0].metadata["file_type"] in ["png", "jpg", "jpeg", "gif", "bmp", "webp", "tif", "tiff"]:
        return chunk_image(doc)
    else:
        return chunk_txt(doc)

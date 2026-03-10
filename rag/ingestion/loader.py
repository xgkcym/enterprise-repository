
from llama_index.core import Document

import os

from config.types import DocumentMetadata


def load_normal_file(path,user_id:str,department:str):
    """获取普通文本Document"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    file_name = path.split('/')[-1]
    file_type =  path.split('.')[-1]
    file_size = os.path.getsize(path)
    return Document(
        text=text,
        id_=f"{department}:{file_name}",
        metadata=DocumentMetadata(
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            user_id=user_id,
            department=department
        )
)


def load_file(path:str,user:str,department:str)-> Document | None:
    if  path.endswith(".txt") or path.endswith('.md') or path.endswith('.doc'):
        return load_normal_file(path,user,department)
    else:
        return None



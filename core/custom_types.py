from dataclasses import Field
from typing import Optional

from pydantic import BaseModel,Field

from core.settings import settings


class DocumentMetadata(BaseModel):
    """文档元数据结构。"""
    file_name:str = Field(default="",description="文件名")
    file_path:str = Field(default="",description="文件路径")
    file_type:str = Field(default="",description="文件类型")
    file_size:int = Field(default=0,description="文件大小")
    source:str = Field(default="",description="文件原型")
    sheet_name:Optional[str] = Field(default="",description="工作簿名")
    section_title:Optional[str] = Field(default="",description="片段标题")
    page:Optional[int] = Field(default=0,description="页面数")
    chunk_index:int= Field(default=0,description="切片序号")

    user_id: int = Field(default="",description="用户ID")
    user_name: str = Field(default="",description="用户名")
    department_id:int = Field(default="",description="部门ID")
    department_name:str = Field(default="",description="部门名称")

    version:int = Field(default=settings.metadata_version ,description="片段标题")



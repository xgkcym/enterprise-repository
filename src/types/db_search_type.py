from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


DBQueryKind = Literal[
    "accessible_departments",
    "accessible_file_count",
    "recent_accessible_files",
    "my_uploaded_files",
    "role_department_scope",
    "unsupported",
]


class DBSearchContext(BaseModel):
    query: Optional[str] = Field(default="", description="原始查询")
    rewritten_query: Optional[str] = Field(default="", description="重写后的查询")
    user_id: Optional[int] = Field(default=None, description="当前用户 ID")
    role_id: Optional[int] = Field(default=None, description="当前角色 ID")
    department_id: Optional[int] = Field(default=None, description="当前部门 ID")
    allowed_department_ids: list[int] = Field(default_factory=list, description="当前用户可访问部门")
    limit: int = Field(default=5, description="列表类查询的返回数量")
    filters: Dict[str, Any] = Field(default_factory=dict, description="结构化过滤条件")

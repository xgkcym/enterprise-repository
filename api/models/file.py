from datetime import datetime

from sqlmodel import SQLModel, Field


class FileModel(SQLModel, table=True):
    __tablename__ = 'file'

    file_id: int = Field(primary_key=True)
    user_id: int = Field(index=True)
    dept_id: int = Field(index=True)
    create_time: datetime = Field(default_factory=datetime.utcnow)
    file_name: str = Field(index=True)
    file_path: str = Field(index=True)
    file_type: str = Field(index=True)
    state:str = Field(default='1',index=True)
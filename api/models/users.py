from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class UserModel(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password: str =  Field(index=True)
    dept_id:int = Field(index=True)
    role_id:int = Field(index=True)
    create_time: datetime = Field(default_factory=datetime.utcnow)
from typing import Optional, Literal, List, Dict
from pydantic import BaseModel, ConfigDict, Field

from src.types.base_type import BaseLLMDecideResult, BaseToolResult
from src.types.rag_type import RagContext, RAGResult


class State(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,  # 赋值时验证类型
        extra="forbid"  # 禁止额外字段，防止拼写错误
    )
    query: Optional[str]

    rewritten_query: Optional[str] = Field(default="",description="重写查询")

    expand_query:List[str] = Field(default=[],description="拓展查询")

    decompose_query:List[str] = Field(default=[],description="子任务规划")

    answer:  Optional[str] = Field(default="",description="回答")

    chat_history:List[str] = Field(default=[],description="短期记忆")

    user_profile:Dict[str,any] = Field(default=None,description="用户画像")

    reason:Optional[str] = Field(default="",description="推断结果")

    tool_request:RagContext | Optional[Dict[str,any]] =  Field(default_factory=lambda:RagContext(),description="工具请求参数")

    tool_result:Optional[BaseToolResult] =  Field(default_factory=lambda :BaseToolResult(),description="工具返回的数据")

    llm_decide_result:Optional[BaseLLMDecideResult] = Field(default_factory=lambda :BaseLLMDecideResult(),description="LLM诊断返回的数据")

    previous_call_tool_request:List[RagContext | Optional[Dict[str,any]]] = Field(default=[],description="历史调用的工具参数")
    previous_call_tool_result:List[Optional[BaseToolResult]] = Field(default=[],description="历史调用的工具结果")

    action:Optional[str] = Field(default="",description="下一步行动")
from typing import Literal, List

from langchain_core.messages import HumanMessage
from pydantic import Field

from src.congfig.llm_config import LLMService
from src.models.llm import deepseek_llm
from src.prompts.agent.deciide_rag import DECIDE_RAG_PROMPT
from src.router.index import route_list
from src.types.agent_state import State
from src.tools.rag_tool import rag_tool
from src.types.base_type import BaseLLMDecideResult
from src.types.rag_type import RAGResult

# class DecodeRagResult(BaseLLMDecideResult):
#     """Agent 决策系统返回的数据"""
#     fail_reason: Literal[
#         "low_recall",
#         "bad_ranking",
#         "ambiguous_query",
#         "no_data",
#     ]  = Field(default=None,description="诊断信息")
#     suggested_actions:List[Literal[
#         "retry",
#         "rewrite",
#         "expand",
#         "decompose",
#         "retrieval",
#         "rerank",
#         "abort"
#     ]] = Field(default=None,description="行为建议")

def rag_node(state:State):
    rag_result:RAGResult = rag_tool(state.tool_request,state.user_profile)
    # ----- 1. 规则层初步判断 -----
    # fail_reason = None
    # if not rag_result.documents or len(rag_result.documents) == 0:
    #     fail_reason = "no_data"
    # elif not rag_result.is_sufficient:
    #     # 简单规则示例
    #     avg_score = sum((d.dense_score or 0.0) for d in rag_result.documents) / max(len(rag_result.documents), 1)
    #     if avg_score < 0.3:
    #         fail_reason = "low_recall"
    #     elif any((d.rerank_score or 0.0) < 0.5 for d in rag_result.documents):
    #         fail_reason = "bad_ranking"
    #     else:
    #         fail_reason = "ambiguous_query"
    #
    # # ----- 2. 构造 LLM prompt （示意） -----
    # # LLM 可进一步生成 confidence / coverage / suggested_actions
    # prompt = DECIDE_RAG_PROMPT.format(
    #     answer=rag_result.answer,
    #     documents=rag_result.documents,
    #     citations=rag_result.citations,
    #     is_sufficient=rag_result.is_sufficient,
    #     reason=rag_result.reason, #是否足够回答理由
    #     attempt=rag_result.attempt,
    #     fail_reason=fail_reason,
    #     route="/".join(route_list)
    # )
    # # 调用 LLM（示意，llm.call 可以换成你实际调用方式）
    # llm_result:DecodeRagResult = LLMService.invoke(
    #     llm=deepseek_llm,
    #     messages=[HumanMessage(content=prompt)],
    #     schema=DecodeRagResult
    # )

    rag_result.attempt = state.tool_result.attempt + 1
    state.previous_call_tool_result.append(rag_result)
    return {
        "answer": rag_result.answer,
        "tool_result": rag_result,
        "previous_call_tool_result":state.previous_call_tool_result
    }

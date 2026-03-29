from langchain_core.messages import HumanMessage

from src.congfig.llm_config import LLMService
from src.models.llm import deepseek_llm
from src.types.agent_state import State
from src.types.base_type import BaseToolResult, BaseLLMDecideResult


def agent_decide_node(state: State):
    result = state.tool_result
    # ✅ 规则层（通用）
    rule_fail_reason = None
    if not result.documents:
        rule_fail_reason = "no_data"
    elif not result.is_sufficient:
        rule_fail_reason = "insufficient"

    # ✅ LLM Prompt（关键：通用，不提 RAG）
    prompt = f"""
    你是企业级Agent决策系统。
    
    工具类型: {result.tool_name}
    Answer: {result.answer}
    Documents: {result.documents}
    Citations: {result.citations}
    是否足够: {result.is_sufficient}
    尝试次数: {result.attempt}
    
    请输出：
    - confidence
    - coverage
    - fail_reason
    - suggested_actions
    - next_action（必须）
    """

    llm_result:BaseLLMDecideResult = LLMService.invoke(
        llm=deepseek_llm,
        messages=[HumanMessage(content=prompt)],
        schema=BaseLLMDecideResult,
    )

    # ✅ 写回
    result.confidence = llm_result.confidence
    result.coverage = llm_result.coverage
    result.fail_reason = llm_result.fail_reason or rule_fail_reason
    result.suggested_actions = llm_result.suggested_actions
    return {
        "tool_result": result,
        "action": llm_result.action
    }
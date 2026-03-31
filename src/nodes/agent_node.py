from typing import Literal

from langchain_core.messages import HumanMessage

from src.congfig.llm_config import LLMService
from src.models.llm import deepseek_llm
from src.prompts.agent.agent import AGENT_PROMPT
from src.router.index import route_list, tool_route, reasoning_route
from src.types.agent_state import State
from src.types.base_type import BaseLLMDecideResult
from src.types.rag_type import RAGResult, RagContext



def agent_node(state: State):


    # ===== 1️⃣ 构建上下文 =====
    last_tool = next((event for event in state.action_history[::-1] if event.kind =="tool"),None)
    last_event = state.action_history[-1]
    if last_event and last_event.kind == "tool" and last_event.output.is_sufficient:
        if verify_task_complete(state,last_tool.output.answer):
            return {
                "action": "finish",
                'answer': last_tool.output.answer,
            }

    ctx = build_agent_context(state)
    allowed_actions = get_allowed_actions(state)
    # ===== 4️⃣ 构建 Prompt =====
    prompt = AGENT_PROMPT.format(
        query=state.query,
        context=ctx,
        query_evolution=build_query_evolution(state),
        allowed_actions=allowed_actions,
    )
    print(prompt)
    # ===== 5️⃣ 调用 LLM =====
    llm_result:BaseLLMDecideResult = LLMService.invoke(
        llm=deepseek_llm,
        messages=[HumanMessage(content=prompt)],
        # 建议你用 schema（非常重要）
        schema=BaseLLMDecideResult
    )



    # ===== 6️⃣ 防御（企业级必须有）=====
    action = llm_result.next_action

    if action not in allowed_actions:
        #强制让选择
        action = allowed_actions[0]


    # 防止死循环（同一工具限制最大调用次数，默认是三次）
    if any(True for item in state.action_history[::-1] if item.name == action and item.attempt >= item.max_attempt):
        action = "finish"

    if action == "finish" or  action == "abort":
        return {
            "action": action,
            "answer": last_tool.output.answer,
            "reason": llm_result.reason,
        }
    return {
        "action": action,
        "reason": llm_result.reason,
    }


def verify_task_complete(state:State,answer:str):
    prompt = f"""
    用户问题:
    {state.query}

    当前答案:
    {answer}

    请判断该答案是否已经完整回答用户问题：

    判断标准：
    1. 是否覆盖所有子问题
    2. 是否缺少关键信息
    3. 是否需要额外查询才能更完整

    只返回：
    true 或 false
    """

    llm_result = LLMService.invoke(
        llm=deepseek_llm,
        messages=[HumanMessage(content=prompt)],
    )
    if isinstance(llm_result.content,str):
        if  llm_result.content.lower() == "true":
            return  True
        else:
            return False
    elif isinstance(llm_result.content,bool):
        return llm_result.content
    else:
        return False



def get_allowed_actions(state:State):

    if not state.action_history:
            return ["rag", "rewrite_query",'normalize_query']

    last_tool = next(
        (e for e in reversed(state.action_history) if e.kind == "tool"),
        None
    )
    if not last_tool:
        return ["rag"]

    last_reasoning_list = []
    for  item in reversed(state.action_history):
        if  item.kind == "reasoning":
            last_reasoning_list.append(item.name)
        else:
            break

    if last_reasoning_list:
        if len(last_reasoning_list) >= 2:
            return tool_route  # 强制获取新信息
        actions = tool_route + reasoning_route
    else:
        output = last_tool.output
        if output.fail_reason == 'no_data': #没有数据
            actions = ["rewrite_query", "expand_query"]
        elif output.fail_reason == "low_recall": # 召回差
            actions = ["expand_query", "rewrite_query","decompose_query"]

        elif output.fail_reason == "ambiguous_query": # query不清晰
            actions = ["rewrite_query","decompose_query","expand_query"]

        elif output.fail_reason == "bad_reranking": # 排序差
            actions = ["decompose_query", "rewrite_query"]

        elif output.fail_reason == 'verification_failed': #验证不通过
            actions = ["rag"]
        else:
            actions = ["rag"]


    actions = [action for action in actions if action not in last_reasoning_list] or ['rag']
    if last_reasoning_list:
        actions = actions
    else:
        actions = actions + ["finish","abort"]
    return  actions

def build_query_evolution(state:State):

    reasoning_events = [
        e for e in state.action_history if e.kind == "reasoning"
    ]

    if not reasoning_events:
        return "无"

    lines = []

    for i, e in enumerate(reasoning_events[-3:]):  # 最多3步
        src = e.input.get("query")
        tgt = ""
        if isinstance(e.output.answer,list) :
            tgt = "|".join(e.output.answer)
        else:
            tgt = e.output.answer

        lines.append(f"Q{i}: {src} → {tgt} ({e.name})")

    lines.append(f"当前查询: {state.working_query}")
    # lines.append(f"当前查询类型: {state.query_type}")

    return "\n".join(lines)


def build_agent_context(state:State,last_tool_num:int = 3) -> str:
    """
    将不同 tool 的 output 转成统一格式
    """
    lines = []
    event_list = [event for event in state.action_history if event.kind == "tool"][:last_tool_num]
    for index,event in enumerate(event_list):
        if event.name == "rag":
            result: RAGResult = event.output  # RAGResult
            tool = {
                "tool_name": "rag",
                "query": event.input,
                "answer": result.answer,
                "fail_reason": result.fail_reason,
                "is_sufficient": result.is_sufficient,
                "quality_hint": {
                    "has_data": len(result.documents) > 0,
                }
            }

            # 未来扩展
        elif event.name == "web":
            result = event.output
            tool = {
                "tool_name": "web",
                "query": event.input,
                "answer": result.answer,
                "fail_reason": result.fail_reason,
                "is_sufficient": result.is_sufficient,
                "quality_hint": {
                    "has_data": len(result.snippets) > 0,
                }
            }

        elif event.name == "db":
            result = event.output
            tool = {
                "tool_name": "db",
                "query": event.input,
                "answer": result.answer,
                "fail_reason": result.fail_reason,
                "is_sufficient": result.is_sufficient,
                "quality_hint": {
                    "has_data": len(result.rows) > 0,

                }
            }
        else:
            tool = {
            "tool_name": event.name,
            "query": "",
            "answer": str(event.output),
            "is_sufficient": False,
            "fail_reason": "",
            "quality_hint": {
                "has_data": True,
            }
        }

        lines.append(
            f"""
            【倒数第{len(event_list)-index}个工具执行】
            工具:{tool["tool_name"]}
            输入:{tool["query"]}
            结果:{tool["answer"]}
            状态:
            - 质量提示: {tool["quality_hint"]}
            - 回答是否足够: {tool["is_sufficient"]}
            - 诊断信息: {tool["fail_reason"]}
            """
        )
    if not lines:
        return  "无"

    return "\n".join(lines)


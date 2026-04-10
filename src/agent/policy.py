from __future__ import annotations

import re

from langchain_core.messages import HumanMessage

from core.settings import settings
from src.config.llm_config import LLMService
from src.models.llm import deepseek_llm
from src.prompts.agent.initial_action import INITIAL_ACTION_PROMPT
from src.types.agent_state import State
from src.types.policy_type import InitialActionDecision, InputGuardDecision, RetrievalPolicyPlan
from src.types.rag_type import RagContext


CURRENT_REASONING_ACTIONS = [
    "rewrite_query",
    "expand_query",
    "decompose_query",
]

CURRENT_TOOL_ACTIONS = [
    "rag",
    "web_search",
    "db_search",
]

FUTURE_TOOL_ACTIONS = [
    "web_search",
    "db_search",
    "export_rag_report",
]

TERMINAL_ACTIONS = ["finish", "abort"]
INITIAL_ACTIONS = {
    "rag",
    "db_search",
    "web_search",
    "rewrite_query",
    "decompose_query",
    "clarify_question",
    "direct_answer",
}


def _should_direct_answer(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if not normalized:
        return False

    direct_markers = [
        "是什么",
        "什么意思",
        "解释一下",
        "介绍一下",
        "怎么理解",
        "如何理解",
        "帮我润色",
        "帮我改写",
        "帮我翻译",
        "帮我总结这句话",
        "what is",
        "explain",
        "introduce",
        "translate",
        "rewrite",
        "polish",
        "summarize this",
    ]
    enterprise_markers = [
        "文档",
        "文件",
        "资料",
        "制度",
        "部门",
        "角色",
        "权限",
        "知识库",
        "上传",
        "公司",
        "内部",
        "report",
        "document",
        "knowledge base",
        "department",
        "permission",
        "uploaded",
        "internal",
    ]

    if _looks_like_external_query(normalized) or _looks_like_structured_db_query(normalized):
        return False
    if any(marker in normalized for marker in enterprise_markers):
        return False
    if any(marker in normalized for marker in direct_markers):
        return True
    return len(normalized) <= 18 and not is_complex_query(normalized)


def _looks_like_external_query(text: str) -> bool:
    """判断查询是否看起来需要外部数据源（如最新资讯、市场动态等）

    通过检查查询文本中是否包含时间敏感或外部数据相关的关键词，来判断是否适合使用外部数据源（如网络搜索）

    Args:
        text: 用户输入的查询文本

    Returns:
        bool: 如果文本包含任何外部数据关键词则返回True，否则返回False
    """
    # 标准化处理：去除前后空格，转换为小写，处理None值
    normalized = (text or "").strip().lower()

    # 定义外部数据查询的关键词列表（包含中英文）
    markers = [
        # 时间相关关键词
        "最新", "最近", "今日", "今天", "本周", "本月", "今年",
        # 资讯类关键词
        "新闻", "公告", "政策", "市场动态",
        # 英文对应关键词
        "latest", "recent", "today", "current", "news", "policy", "market update",
    ]

    # 检查标准化后的文本是否包含任何定义的关键词
    return any(marker in normalized for marker in markers)


def _looks_like_structured_db_query(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if not normalized:
        return False

    file_terms = ["文件", "文档", "资料", "上传", "file", "document", "uploaded"]
    dept_terms = ["部门", "department", "科室", "组织"]
    role_terms = ["角色", "role", "岗位"]
    permission_terms = ["权限", "可访问", "访问范围", "scope", "permission", "accessible"]
    list_terms = ["多少", "数量", "几个", "几条", "列表", "清单", "最近", "最新", "有哪些", "哪些", "count", "how many", "list", "recent", "latest"]
    first_person_terms = ["我", "我的", "我能", "我可以", "my", "mine", "当前用户"]

    mentions_file = any(term in normalized for term in file_terms)
    mentions_department = any(term in normalized for term in dept_terms)
    mentions_role = any(term in normalized for term in role_terms)
    mentions_permission = any(term in normalized for term in permission_terms)
    mentions_list_intent = any(term in normalized for term in list_terms)
    mentions_first_person = any(term in normalized for term in first_person_terms)

    if mentions_role and (mentions_department or mentions_permission):
        return True
    if mentions_department and (mentions_permission or mentions_first_person or mentions_list_intent):
        return True
    if mentions_file and (mentions_list_intent or mentions_first_person):
        return True
    if mentions_permission and mentions_first_person:
        return True
    return False


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _is_illegal_cyber_query(text: str) -> bool:
    malicious_verbs = [
        "盗取",
        "窃取",
        "破解",
        "爆破",
        "撞库",
        "绕过",
        "入侵",
        "攻击",
        "挂马",
        "投毒",
        "勒索",
        "注入攻击",
        "steal",
        "hack",
        "exploit",
        "bypass",
        "exfiltrate",
        "phish",
        "malware",
        "ransomware",
    ]
    cyber_targets = [
        "密码",
        "账号",
        "cookie",
        "token",
        "凭证",
        "数据库",
        "后台",
        "服务器",
        "内网",
        "权限",
        "验证码",
        "系统",
        "password",
        "credential",
        "account",
        "admin",
        "database",
        "server",
        "internal network",
    ]
    return _contains_any(text, malicious_verbs) and _contains_any(text, cyber_targets)


def _is_privacy_exfiltration_query(text: str) -> bool:
    exfiltration_verbs = [
        "批量导出",
        "批量获取",
        "爬取",
        "倒库",
        "导出全部",
        "收集",
        "泄露",
        "卖掉",
        "dump",
        "scrape",
        "export all",
        "bulk extract",
    ]
    sensitive_targets = [
        "身份证",
        "手机号",
        "住址",
        "银行卡",
        "邮箱",
        "家庭地址",
        "人脸",
        "隐私",
        "客户名单",
        "employee list",
        "phone number",
        "id card",
        "bank card",
        "personal data",
        "pii",
    ]
    return _contains_any(text, exfiltration_verbs) and _contains_any(text, sensitive_targets)


def _is_illegal_deception_query(text: str) -> bool:
    deception_markers = [
        "钓鱼邮件",
        "钓鱼网站",
        "伪造合同",
        "伪造公章",
        "骗过审核",
        "假发票",
        "social engineering",
        "phishing email",
        "fake invoice",
        "fake contract",
        "bypass review",
    ]
    return _contains_any(text, deception_markers)


def guard_input(query: str) -> InputGuardDecision:
    """输入守卫检查函数，用于验证用户输入的合法性

    Args:
        query: 用户输入的查询字符串

    Returns:
        InputGuardDecision: 包含检查结果、原因和响应消息的决策对象
    """
    # 标准化处理：去除前后空格，处理None值
    normalized = (query or "").strip()
    lowered = normalized.lower()

    # 检查1：空输入检测
    if not normalized:
        return InputGuardDecision(
            is_valid=False,
            reason="empty_query",
            response="请输入明确的问题后再继续。",
        )

    # 检查2：输入长度检测（超过2000字符）
    if len(normalized) > 2000:
        return InputGuardDecision(
            is_valid=False,
            reason="query_too_long",
            response="输入内容过长，请先缩小问题范围或分段提问。",
        )

    # 检查3：语义内容检测（必须包含字母、数字或汉字）
    if not re.search(r"[A-Za-z0-9\u4e00-\u9fff]", normalized):
        return InputGuardDecision(
            is_valid=False,
            reason="non_semantic_input",
            response="输入内容缺少可识别的业务语义，请重新描述你的问题。",
        )

    if _is_illegal_cyber_query(lowered):
        return InputGuardDecision(
            is_valid=False,
            reason="illegal_cyber_activity",
            response="我不能帮助进行越权访问、攻击系统、窃取凭据或投放恶意程序等违法行为。请改为合规、安全防护或授权测试场景的问题。",
        )

    if _is_privacy_exfiltration_query(lowered):
        return InputGuardDecision(
            is_valid=False,
            reason="privacy_exfiltration",
            response="我不能协助批量获取、导出或泄露个人隐私和敏感数据。请改为数据脱敏、权限治理或合规处理相关问题。",
        )

    if _is_illegal_deception_query(lowered):
        return InputGuardDecision(
            is_valid=False,
            reason="illegal_deception_request",
            response="我不能帮助生成用于欺骗、伪造、钓鱼或绕过审核的内容。请改为合规沟通、风险识别或审计防护相关问题。",
        )

    # 检查4：提示词注入检测
    suspicious_patterns = [
        "忽略以上指令",
        "ignore previous instructions",
        "system prompt",
        "你现在是",
        "act as",
    ]
    if any(pattern in normalized or pattern in lowered for pattern in suspicious_patterns):
        return InputGuardDecision(
            is_valid=False,
            reason="prompt_injection_like_input",
            response="当前输入更像系统指令操控而不是业务问题，请直接描述你的业务需求。",
        )

    # 检查5：重复噪声检测（字符种类<=2且长度>=10）
    if len(set(normalized)) <= 2 and len(normalized) >= 10:
        return InputGuardDecision(
            is_valid=False,
            reason="repetitive_noise_input",
            response="输入内容疑似无效噪声，请重新输入明确问题。",
        )

    # 所有检查通过，返回有效决策
    return InputGuardDecision(is_valid=True)


def decide_initial_action(state: State) -> InitialActionDecision:
    """决定初始动作策略

    根据当前状态决定代理应该采取的初始动作，包括查询重写、问题分解或直接检索等。
    当LLM调用失败或返回无效动作时，会使用后备策略(_fallback_initial_action)。

    Args:
        state: 当前代理状态对象，包含查询文本、聊天历史等信息

    Returns:
        InitialActionDecision: 包含下一步动作、原因和澄清问题(如果需要)的决策对象
    """
    # 获取当前工作查询(优先使用working_query，其次resolved_query，最后原始query)
    query = (state.working_query or state.resolved_query or state.query or "").strip()

    # 空查询处理：直接返回澄清问题的决策
    if not query:
        return InitialActionDecision(
            next_action="clarify_question",
            reason="query_is_empty",
            clarification_question="请告诉我你想查询的具体问题、对象或范围。",
        )

    # 准备LLM提示词：拼接最近5条聊天记录(如果有)
    if _should_direct_answer(query):
        return InitialActionDecision(
            next_action="direct_answer",
            reason="direct_llm_answer_preferred",
        )

    chat_history = "\n".join(state.chat_history[-5:]) if state.chat_history else ""
    prompt = INITIAL_ACTION_PROMPT.format(query=query, chat_history=chat_history)

    try:
        # 调用LLM服务获取初始动作决策
        decision: InitialActionDecision = LLMService.invoke(
            llm=deepseek_llm,
            messages=[HumanMessage(content=prompt)],
            schema=InitialActionDecision,
        )
    except Exception:
        # LLM调用失败时使用后备策略
        decision = _fallback_initial_action(query)

    # 验证LLM返回的动作是否在允许的初始动作集合中
    if decision.next_action not in INITIAL_ACTIONS:
        decision = _fallback_initial_action(query)

    # 如果动作是需要澄清问题但缺少澄清内容，设置默认澄清问题
    if decision.next_action == "clarify_question" and not decision.clarification_question:
        decision.clarification_question = "你的问题里缺少关键主体或范围。请补充你想查询的对象、时间范围或具体目标。"

    # 确保决策对象包含原因字段
    if not decision.reason:
        decision.reason = "initial_action_selected"

    return decision


def _fallback_initial_action(query: str) -> InitialActionDecision:
    if _should_direct_answer(query):
        return InitialActionDecision(
            next_action="direct_answer",
            reason="fallback_direct_answer",
        )
    if _looks_like_structured_db_query(query):
        return InitialActionDecision(
            next_action="db_search",
            reason="fallback_structured_db_query",
        )
    if _looks_like_external_query(query):
        return InitialActionDecision(
            next_action="web_search",
            reason="fallback_external_query",
        )
    if is_complex_query(query):
        return InitialActionDecision(
            next_action="decompose_query",
            reason="fallback_complex_query",
        )
    if needs_rewrite_first(query):
        return InitialActionDecision(
            next_action="rewrite_query",
            reason="fallback_needs_rewrite",
        )
    return InitialActionDecision(
        next_action="rag",
        reason="fallback_direct_rag",
    )


def get_allowed_actions(state: State) -> list[str]:
    """获取当前状态下允许执行的动作列表

    根据状态历史记录中的推理和工具使用情况，动态决定下一步可用的动作集合。
    主要逻辑：
    1. 如果没有推理历史，则决定初始动作
    2. 根据最近工具使用的失败原因决定后续动作
    3. 避免重复执行相同类型的推理动作

    Args:
        state: 当前代理状态对象，包含动作历史等信息

    Returns:
        list[str]: 允许执行的动作名称列表
    """
    current_query = state.working_query or state.resolved_query or state.query or ""

    # 获取所有历史中的推理类型动作
    reasoning_history = [event for event in state.action_history if event.kind == "reasoning" and event.name != "resolved_query"]
    if not reasoning_history:
        # 如果没有推理历史，则决定初始动作
        initial_actions = [decide_initial_action(state).next_action]
        if _should_direct_answer(current_query):
            initial_actions.append("direct_answer")
        initial_actions.append("rag")
        if _looks_like_external_query(current_query):
            initial_actions.append("web_search")
        if _looks_like_structured_db_query(current_query):
            initial_actions.append("db_search")
        return list(dict.fromkeys(initial_actions))

    # 查找最近使用的工具动作
    last_tool = next((event for event in reversed(state.action_history) if event.kind == "tool"), None)
    if not last_tool:
        # 如果没有工具使用历史，默认返回RAG动作
        actions = ["rag", "rewrite_query", "expand_query", "decompose_query"]
        if _should_direct_answer(current_query):
            actions.insert(0, "direct_answer")
        if _looks_like_external_query(current_query):
            actions.append("web_search")
        if _looks_like_structured_db_query(current_query):
            actions.append("db_search")
        return list(dict.fromkeys(actions))

    # 收集最近连续执行的推理动作（从最近开始倒序检查）
    trailing_reasoning = []
    for item in reversed(state.action_history):
        if item.kind == "reasoning":
            trailing_reasoning.append(item.name)
        else:
            break

    if trailing_reasoning:
        # 如果有连续推理动作
        if len(trailing_reasoning) >= 2:
            # 连续2次以上推理后，只允许工具动作
            actions = list(CURRENT_TOOL_ACTIONS)
            if _looks_like_external_query(current_query):
                actions.append("web_search")
            if _looks_like_structured_db_query(current_query):
                actions.append("db_search")
            return list(dict.fromkeys(actions))
        # 否则允许工具+推理动作
        actions = list(CURRENT_TOOL_ACTIONS) + list(CURRENT_REASONING_ACTIONS)
    else:
        # 根据最近工具动作的失败原因决定后续动作
        fail_reason = getattr(last_tool.output, "fail_reason", None)
        if fail_reason == "no_data":
            actions = ["rewrite_query", "expand_query", "rag", "web_search"]
            if _looks_like_structured_db_query(current_query):
                actions.append("db_search")
        elif fail_reason == "low_recall":
            actions = ["expand_query", "rewrite_query", "decompose_query", "rag", "web_search"]
            if _looks_like_structured_db_query(current_query):
                actions.append("db_search")
        elif fail_reason == "ambiguous_query":
            actions = ["rewrite_query", "decompose_query", "expand_query", "rag"]
        elif fail_reason in {"bad_ranking", "bad_reranking"}:
            actions = ["decompose_query", "rewrite_query", "expand_query", "rag"]
        elif fail_reason == "verification_failed":
            actions = ["rewrite_query", "expand_query", "rag"]
        else:
            actions = ["rag", "rewrite_query", "expand_query"]

    if _looks_like_external_query(current_query) and "web_search" not in actions:
        actions.append("web_search")
    if _looks_like_structured_db_query(current_query) and "db_search" not in actions:
        actions.append("db_search")
    if _should_direct_answer(current_query) and "direct_answer" not in actions and not last_tool:
        actions.insert(0, "direct_answer")

    # 过滤掉已经连续执行过的推理动作
    actions = [action for action in actions if action not in trailing_reasoning] or ["rag"]
    # 如果没有连续推理动作，则添加终止动作选项
    if not trailing_reasoning:
        actions.extend(TERMINAL_ACTIONS)
    return actions


def should_force_finish(state: State) -> tuple[bool, str | None]:
    """判断是否应该强制终止当前流程

    根据状态历史记录中的RAG操作结果和查询处理情况，决定是否应该提前终止流程。
    主要检查以下情况：
    1. 连续两次RAG操作失败且失败原因相同
    2. 在重写和扩展查询后仍然无法获取数据
    3. 分解查询路径已穷尽但仍失败

    Args:
        state: 当前代理状态对象，包含动作历史等信息

    Returns:
        tuple[bool, str | None]:
            - 第一个元素表示是否应该强制终止
            - 第二个元素是终止原因描述字符串，如果不需要终止则为None
    """
    # 获取最近的非resolved_query事件和事件名称列表
    recent_events = [event for event in state.action_history if event.name != "resolved_query"]
    recent_names = [event.name for event in recent_events]
    # 筛选出所有的工具事件
    lasts_tools = [event for event in reversed(recent_events) if event.kind == "tool"]
    last_rag_result = state.last_rag_result


    # 检查1：连续两次工具失败且失败原因相同
    if len(lasts_tools) >= 2 and lasts_tools[-1].name == lasts_tools[-2].name:
        last_two_fail_reasons = [
            getattr(event.output, "fail_reason", None)
            for event in lasts_tools[-2:]
        ]
        if last_two_fail_reasons[0] == last_two_fail_reasons[1]:
            if last_two_fail_reasons[0] in {"no_data", "low_recall", "bad_ranking", "tool_error"}:
                        return True, f"repeated_{lasts_tools[0].name}_failure:{last_two_fail_reasons[0]}"

    # 检查2：在重写和扩展查询后仍然无法获取数据
    if last_rag_result and last_rag_result.fail_reason == "no_data":
        if "rewrite_query" in recent_names and "expand_query" in recent_names and recent_names.count("rag") >= 2:
            return True, "rag_exhausted_after_rewrite_expand"

    # 检查3：分解查询路径已穷尽但仍失败
    if state.decompose_query and state.sub_query_results and last_rag_result:
        if last_rag_result.fail_reason in {"no_data", "tool_error"}:
            return True, f"decompose_path_exhausted:{last_rag_result.fail_reason}"

    # 默认返回不终止
    return False, None


def is_complex_query(query: str) -> bool:
    lowered = query.lower()
    complex_markers = [
        "对比",
        "比较",
        "分析",
        "总结",
        "方案",
        "风险",
        "以及",
        "并且",
        "同时",
        "怎么做",
        "如何做",
    ]
    punctuation_count = sum(query.count(symbol) for symbol in ["，", ",", "；", ";", "。"])
    if len(query) >= 30 and punctuation_count >= 1:
        return True
    if punctuation_count >= 2:
        return True
    return any(marker in lowered or marker in query for marker in complex_markers)


def needs_rewrite_first(query: str) -> bool:
    lowered = query.lower()
    vague_markers = [
        "这个",
        "那个",
        "咋",
        "怎么看",
        "怎么弄",
        "如何看",
        "它",
    ]
    if len(query) <= 8:
        return True
    return any(marker in lowered or marker in query for marker in vague_markers)


def build_retrieval_plan(state: State, previous_context: RagContext | None = None) -> RetrievalPolicyPlan:
    retrieval_top_k = previous_context.retrieval_top_k if previous_context else settings.retriever_top_k
    rerank_top_k = previous_context.rerank_top_k if previous_context else settings.reranker_top_k
    use_retrieval = True if previous_context is None else previous_context.use_retrieval
    use_rerank = True if previous_context is None else previous_context.use_rerank

    needs_more_recall = False
    needs_more_precision = False
    strategy_reason = "default_rag_strategy"

    last_result = state.last_rag_result
    if not last_result:
        return RetrievalPolicyPlan(
            retrieval_top_k=retrieval_top_k,
            rerank_top_k=rerank_top_k,
            use_retrieval=use_retrieval,
            use_rerank=use_rerank,
            needs_more_recall=needs_more_recall,
            needs_more_precision=needs_more_precision,
            strategy_reason=strategy_reason,
        )

    fail_reason = last_result.fail_reason
    if fail_reason in {"no_data", "low_recall"}:
        retrieval_top_k = max(retrieval_top_k, settings.retriever_top_k) + 3
        use_retrieval = True
        use_rerank = True
        needs_more_recall = True
        strategy_reason = "increase_recall_after_sparse_results"
    elif fail_reason in {"bad_ranking", "verification_failed"}:
        rerank_top_k = max(rerank_top_k, settings.reranker_top_k) + 2
        use_retrieval = False
        use_rerank = True
        needs_more_precision = True
        strategy_reason = "increase_precision_after_ranking_issue"
    elif fail_reason == "ambiguous_query":
        use_retrieval = True
        use_rerank = True
        strategy_reason = "query_is_ambiguous_retry_after_query_transform"

    return RetrievalPolicyPlan(
        retrieval_top_k=retrieval_top_k,
        rerank_top_k=rerank_top_k,
        use_retrieval=use_retrieval,
        use_rerank=use_rerank,
        needs_more_recall=needs_more_recall,
        needs_more_precision=needs_more_precision,
        strategy_reason=strategy_reason,
    )

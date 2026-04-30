from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Sequence


ActionCategory = Literal["tool", "reasoning", "terminal", "response"]


@dataclass(frozen=True)
class ActionSpec:
    name: str
    category: ActionCategory
    summary: str
    when_to_use: str
    when_not_to_use: str = ""


ACTION_REGISTRY: dict[str, ActionSpec] = {
    "rag": ActionSpec(
        name="rag",
        category="tool",
        summary="从企业知识库检索叙述性证据。",
        when_to_use="适用于内部文档、报告、制度、已上传文件，以及需要文档证据支撑的一般问答。",
        when_not_to_use="不适用于结构化字段查询、公开实时信息或金融事实图谱推理。",
    ),
    "graph_rag": ActionSpec(
        name="graph_rag",
        category="tool",
        summary="查询金融事实图谱中的指标、实体关系和跨报告事实。",
        when_to_use="适用于财务指标比较、趋势分析、实体与事件关系、关联方交易，或跨报告事实关联。",
        when_not_to_use="不适用于普通叙述性文档问答或非金融类内部制度问题。",
    ),
    "web_search": ActionSpec(
        name="web_search",
        category="tool",
        summary="从网页检索公开且具有时效性的信息。",
        when_to_use="适用于最新新闻、近期市场动态、当前政策变化和外部公开信息。",
        when_not_to_use="不适用于内部文档、已上传文件或企业私有数据。",
    ),
    "db_search": ActionSpec(
        name="db_search",
        category="tool",
        summary="查询结构化内部记录和字段。",
        when_to_use="适用于数量、列表、权限、归属映射、上传记录和结构化业务字段。",
        when_not_to_use="不适用于需要文档证据的开放式叙述问答。",
    ),
    "rewrite_query": ActionSpec(
        name="rewrite_query",
        category="reasoning",
        summary="将查询改写为更清晰、更适合检索的形式。",
        when_to_use="适用于表述模糊、口语化、范围不足，或过度依赖上文的问题。",
        when_not_to_use="不适用于已经精确且可直接检索的问题。",
    ),
    "expand_query": ActionSpec(
        name="expand_query",
        category="reasoning",
        summary="扩展查询以提高召回。",
        when_to_use="适用于召回范围过窄，需要补充更多相关检索表达的情况。",
        when_not_to_use="不适用于精度比召回更重要，或查询已经足够宽泛的情况。",
    ),
    "decompose_query": ActionSpec(
        name="decompose_query",
        category="reasoning",
        summary="将复杂请求拆分为更小的子问题。",
        when_to_use="适用于多部分分析、比较、分步规划，或包含多个明确目标的请求。",
        when_not_to_use="不适用于简短且目标单一的问题。",
    ),
    "direct_answer": ActionSpec(
        name="direct_answer",
        category="response",
        summary="不调用检索工具，直接回答用户问题。",
        when_to_use="适用于仅凭通用知识和当前对话上下文即可安全回答，且不需要企业证据或实时信息的问题。",
        when_not_to_use="不适用于内部知识检索、结构化数据查询或具有时效性的外部问题。",
    ),
    "clarify_question": ActionSpec(
        name="clarify_question",
        category="response",
        summary="请用户澄清缺失的范围或主体。",
        when_to_use="适用于请求信息过少或过于模糊，无法安全继续处理的情况。",
        when_not_to_use="不适用于系统可以基于合理假设继续处理的情况。",
    ),
    "finalize": ActionSpec(
        name="finalize",
        category="terminal",
        summary="基于已检索证据撰写最终答案。",
        when_to_use="适用于已经收集到足够证据，可以综合生成回复的情况。",
        when_not_to_use="不适用于证据缺口仍然明显的情况。",
    ),
    "finish": ActionSpec(
        name="finish",
        category="terminal",
        summary="停止工作流，并返回当前最合适的答案或兜底回复。",
        when_to_use="适用于没有更高价值的下一步动作，或工作流已耗尽的情况。",
        when_not_to_use="不适用于其他允许动作仍可能补充有效证据的情况。",
    ),
    "abort": ActionSpec(
        name="abort",
        category="terminal",
        summary="终止本次运行，不再执行后续动作。",
        when_to_use="仅适用于必须停止或工作流状态无效的情况。",
        when_not_to_use="不要作为常规回答路径使用。",
    ),
}


REASONING_ACTION_NAMES: tuple[str, ...] = (
    "rewrite_query",
    "expand_query",
    "decompose_query",
)

TOOL_ACTION_NAMES: tuple[str, ...] = (
    "rag",
    "graph_rag",
    "web_search",
    "db_search",
)

TERMINAL_ACTION_NAMES: tuple[str, ...] = (
    "finish",
    "abort",
)

INITIAL_ACTION_NAMES: tuple[str, ...] = (
    "rag",
    "graph_rag",
    "db_search",
    "web_search",
    "rewrite_query",
    "decompose_query",
    "clarify_question",
    "direct_answer",
)

ROUTE_ACTION_NAMES: tuple[str, ...] = (
    *REASONING_ACTION_NAMES,
    *TOOL_ACTION_NAMES,
    "finalize",
    "abort",
    "finish",
    "direct_answer",
)


def dedupe_action_names(names: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        if not name or name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return ordered


def get_action_spec(action_name: str) -> ActionSpec:
    return ACTION_REGISTRY[action_name]


def render_action_catalog(action_names: Sequence[str]) -> str:
    lines: list[str] = []
    for action_name in dedupe_action_names(action_names):
        spec = get_action_spec(action_name)
        lines.append(
            f"- {spec.name}: {spec.summary} 适用场景：{spec.when_to_use} 不适用场景：{spec.when_not_to_use or '无'}"
        )
    return "\n".join(lines) if lines else "无"

QA_GENERATION_PROMPT = """
你正在为企业级 RAG 系统准备高精度 QA 基准数据。

任务：
只有当答案能够严格基于提供的节点时，才生成 QA 条目。

要求：
1. 精度比召回更重要。如果证据薄弱、模糊、重复或质量较低，返回空的 `qa_list`。
2. 每个问题都必须至少需要 2 个节点才能回答。
3. 每个答案都必须完全由提供的节点支持。不要添加假设、背景知识、隐藏原因或未说明的时间范围。
4. 优先生成答案简短、具体的事实型或比较型问题。
5. 只有当结论被节点明确支持时，才生成分析型问题。
6. 使用与源文档相同的语言。目标语言：`{source_language}`。
7. 不要翻译成其他语言。
8. `node_ids` 只能包含支撑答案所需的最少节点。
9. 如果问题可以由单个节点回答，不要生成该问题。
10. 如果答案包含数字、日期、比例、实体或其他事实值，该值必须在节点中明确出现。
11. 最多生成 `{max_qa_per_batch}` 条 QA。
12. `difficulty` 必须是以下值之一：`easy`、`medium`、`hard`。
13. `intent` 必须是以下值之一：`factoid`、`comparison`、`analysis`。
14. 仅输出 JSON。

节点：
{nodes}

输出 JSON：
{{
  "qa_list": [
    {{
      "question": "...",
      "answer": "...",
      "language": "{source_language}",
      "difficulty": "easy",
      "intent": "factoid",
      "node_ids": ["node1", "node2"]
    }}
  ]
}}
"""

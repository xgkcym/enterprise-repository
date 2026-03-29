DECIDE_RAG_PROMPT = """
你是一个企业级 Agent 决策系统。
根据以下信息分析：
- Answer: {answer}
- 文档列表 (node_id + (dense_score(语义召回分数) / bm25_score(关键字召回分数)) + rerank_score + content(片段)): {documents}
- citations: {citations}
- 是否足够回答: {is_sufficient}
- 是否足够回答理由:{reason}
- 参考fail_reason:{fail_reason}，但如果你认为不合理，可以修正
- 历史尝试次数: {attempt}

要求：
1. 输出格式必须是JSON格式

---

[输出字段说明]

1. confidence (0~1)
2. coverage (0~1)
3. fail_reason (low_recall / bad_ranking / ambiguous_query / no_data):
4. suggested_actions (列表: rewrite / expand / retry / finish / abort )
5. 下一步 next_action (用于 Router) (列表: {route} )(如果无法判断则返回空)

---

输出JSON：
{{
    "confidence":0,
    "coverage":0,
    "fail_reason":"...",
    "suggested_actions":["...","..."],
    "next_action":""
}}

只输出JSON，不要解释。
"""

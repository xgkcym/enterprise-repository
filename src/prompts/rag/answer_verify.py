VERIFY_PROMPT = """
请判断以下回答是否完全基于context。

【规则】
1. 如果回答包含context中没有的信息 → false
2. 如果引用不正确 → false
3. 如果回答正确 → true
4. 输出格式必须是JSON格式
---

【context】
{context}

【answer】
{answer}

---

输出JSON：

{{
  "valid": true/false
}}

只输出JSON格式数据，不要解释。
"""
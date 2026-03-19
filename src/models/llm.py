from llama_index.llms.deepseek import DeepSeek
from llama_index.llms.openai import OpenAI

from core.settings import settings

deepseek_llm = DeepSeek(
    model=settings.deepseek_model,
    api_key=settings.deepseek_api_key
)

chatgpt_llm = OpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key
)

if __name__ == "__main__":
    res = chatgpt_llm.chat([
        {
            "role": "user",
            "content":"请你一句话回答什么是机器学习？"
        }
    ])
    print(res)
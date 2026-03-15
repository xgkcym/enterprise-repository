from llama_index.llms.deepseek import DeepSeek
from llama_index.core.llms import ChatMessage

from core.settings import settings

deepseek_llm = DeepSeek(
    model=settings.deepseek_model,
    api_key=settings.deepseek_key
)
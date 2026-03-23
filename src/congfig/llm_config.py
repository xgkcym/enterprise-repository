import json
import time
from typing import Optional, Type

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel

from core.settings import settings
from src.models.llm import chatgpt_llm
from utils.logger_handler import logger




class LLMService:


    @staticmethod
    def invoke(llm: BaseChatModel,messages,schema:Optional[Type[BaseModel]] = None,fallback_llm:BaseChatModel = None):
        last_exception = None
        for i in range(settings.max_retries):
            try:
                start = time.time()
                response = llm.invoke(messages)
                duration = time.time() - start
                if duration > settings.max_timeout:
                    logger.warning(f"[LLM超时] 耗时: {duration:.2f}s")
                else:
                    logger.info(f"[LLM调用成功] 耗时: {duration:.2f}s")

                usage = response.response_metadata.get("token_usage", {})
                logger.info(f"[tokens]: {usage}")
                print(response)
                if schema:
                    try:
                        content = response.content
                        data = json.loads(content)
                        return schema(**data)
                    except Exception:
                        raise Exception(f"[LLM格式返回失败]：\n返回信息:f{response} \n需要的格式化:{schema}")
                return response
            except Exception as e:
                last_exception = e
                logger.warning(f"[LLM失败] 第{i + 1}次: {e}")
                time.sleep(2 ** i)


        # 重试失败以后换大模型输出
        if not fallback_llm:
            fallback_llm = chatgpt_llm
        try:
            start = time.time()
            response = fallback_llm.invoke(messages)
            duration = time.time() - start
            if duration > settings.max_timeout:
                logger.warning(f"[FallbackLLM超时] 耗时: {duration:.2f}s")
            else:
                logger.info(f"[FallbackLLM调用成功] 耗时: {duration:.2f}s")
            if schema and not isinstance(response, schema):
                raise Exception(f"[FallbackLLM格式返回失败]：\n返回信息:f{response} \n需要的格式化:{schema}")
            return response
        except Exception as e:
            last_exception = e
            raise last_exception



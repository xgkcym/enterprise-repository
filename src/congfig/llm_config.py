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
        if schema:
            llm = llm.with_structured_output(schema, include_raw=True)
        for i in range(settings.max_retries):
            try:
                start = time.time()
                response = llm.invoke(messages)
                duration = time.time() - start
                if duration > settings.max_timeout:
                    logger.warning(f"[LLM超时] 耗时: {duration:.2f}s")
                else:
                    logger.info(f"[LLM调用成功] 耗时: {duration:.2f}s")

                usage = response['raw'].response_metadata.get("token_usage", {})
                logger.info(f"[tokens]: {usage}")

                if schema:
                    print(response['parsed'])
                    return response['parsed']
                print(response['raw'])
                return response['raw']
            except Exception as e:
                last_exception = e
                logger.warning(f"[LLM失败] 第{i + 1}次: {e}")
                time.sleep(2 ** i)


        # 重试失败以后换大模型输出
        if not fallback_llm:
            fallback_llm = chatgpt_llm

        if schema:
            fallback_llm = fallback_llm.with_structured_output(schema, include_raw=True)
        try:
            start = time.time()
            response = fallback_llm.invoke(messages)
            duration = time.time() - start
            if duration > settings.max_timeout:
                logger.warning(f"[LLM超时] 耗时: {duration:.2f}s")
            else:
                logger.info(f"[LLM调用成功] 耗时: {duration:.2f}s")

            usage = response['raw'].response_metadata.get("token_usage", {})
            logger.info(f"[tokens]: {usage}")

            if schema:
                print(response['parsed'])
                return response['parsed']
            print(response['raw'])
            return response['raw']
        except Exception as e:
            last_exception = e
            raise last_exception



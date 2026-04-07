from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator
from uuid import uuid4

from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from core.settings import settings
from service.database.connect import get_session
from service.dependencies.auth import get_current_active_user
from service.models.role_department import RoleDepartmentModel
from service.models.users import UserModel
from service.router.agent.index import agent_router
from service.utils.chat_store import chat_store
from src.agent.runner import build_run_report, run_agent


class ChatStreamRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query")
    session_id: str | None = Field(default=None, description="Existing session id")


def build_user_profile(current_user: UserModel, allowed_department_ids: list[int]) -> dict:
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "dept_id": current_user.dept_id,
        "department_id": current_user.dept_id,
        "role_id": current_user.role_id,
        "allowed_department_ids": allowed_department_ids,
    }


def _chunk_text(text: str, chunk_size: int = 16) -> list[str]:
    value = text or ""
    if not value:
        return []
    return [value[i : i + chunk_size] for i in range(0, len(value), chunk_size)]


def _format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _build_allowed_department_ids(
    *,
    current_user: UserModel,
    session: AsyncSession,
) -> list[int]:
    role_dept_result = await session.execute(
        select(RoleDepartmentModel.dept_id).where(RoleDepartmentModel.role_id == current_user.role_id)
    )
    return role_dept_result.scalars().all()


@agent_router.get("/sessions")
async def list_chat_sessions(current_user: UserModel = Depends(get_current_active_user)):
    sessions = await asyncio.to_thread(chat_store.list_sessions, user_id=int(current_user.id))
    return {"code": 200, "message": "success", "data": sessions}


@agent_router.get("/sessions/{session_id}/messages")
async def get_chat_session_messages(
    session_id: str,
    current_user: UserModel = Depends(get_current_active_user),
):
    session_doc = await asyncio.to_thread(
        chat_store.get_session,
        session_id=session_id,
        user_id=int(current_user.id),
    )
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await asyncio.to_thread(
        chat_store.list_messages,
        session_id=session_id,
        user_id=int(current_user.id),
    )
    return {"code": 200, "message": "success", "data": {"session": session_doc, "messages": messages}}


@agent_router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: UserModel = Depends(get_current_active_user),
):
    deleted = await asyncio.to_thread(
        chat_store.soft_delete_session,
        session_id=session_id,
        user_id=int(current_user.id),
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"code": 200, "message": "success", "data": {"session_id": session_id}}


@agent_router.post("/chat/stream")
async def stream_chat(
    payload: ChatStreamRequest,
    current_user: UserModel = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """处理聊天流请求的接口

    Args:
        payload: 包含用户查询和会话ID的请求体
        current_user: 当前已认证用户对象
        session: 异步数据库会话

    Returns:
        StreamingResponse: 服务器发送事件(SSE)流式响应
    """
    # 清理并验证用户查询
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    # 获取用户有权限访问的部门ID列表
    allowed_department_ids = await _build_allowed_department_ids(current_user=current_user, session=session)
    # 构建用户信息字典
    user_profile = build_user_profile(current_user, allowed_department_ids)
    current_session_id = payload.session_id

    # 如果提供了会话ID，验证会话是否存在
    if current_session_id:
        session_doc = await asyncio.to_thread(
            chat_store.get_session,
            session_id=current_session_id,
            user_id=int(current_user.id),
        )
        if not session_doc:
            raise HTTPException(status_code=404, detail="Session not found")

    async def event_stream() -> AsyncIterator[str]:
        """生成服务器发送事件(SSE)的异步生成器

        生成的事件包括:
        - session_created: 新会话创建
        - message_started: 开始生成回复
        - token: 回复内容分块
        - message_completed: 回复完成
        - error: 错误信息
        """
        nonlocal current_session_id
        try:
            # 如果没有会话ID，创建新会话
            if not current_session_id:
                session_doc = await asyncio.to_thread(
                    chat_store.create_session,
                    user_id=int(current_user.id),
                    first_query=query,
                )
                current_session_id = session_doc["session_id"]
                yield _format_sse("session_created", session_doc)

            # 保存用户消息到存储
            await asyncio.to_thread(
                chat_store.create_message,
                session_id=current_session_id,
                user_id=int(current_user.id),
                role="user",
                content=query,
            )

            # 生成助理消息ID并发送开始事件
            assistant_message_id = str(uuid4())
            yield _format_sse(
                "message_started",
                {
                    "session_id": current_session_id,
                    "role": "assistant",
                    "message_id": assistant_message_id,
                },
            )

            # 运行AI代理生成回复
            final_state = await asyncio.to_thread(
                run_agent,
                query,
                user_id=str(current_user.id or ""),
                session_id=current_session_id,
                user_profile=user_profile,
                max_steps=settings.agent_max_steps,
            )
            # 构建运行报告并提取回答和引用
            report = build_run_report(final_state)
            answer = (report.get("answer") or "").strip()
            citations = report.get("citations") or []
            if not answer:
                answer = report.get("reason") or "未生成有效回答。"

            # 创建并保存助理消息
            draft_message = await asyncio.to_thread(
                chat_store.create_message,
                session_id=current_session_id,
                user_id=int(current_user.id),
                role="assistant",
                content=answer,
                citations=citations,
                message_id=assistant_message_id,
            )

            # 创建运行记录并关联到消息
            run_doc = await asyncio.to_thread(
                chat_store.create_run,
                session_id=current_session_id,
                user_id=int(current_user.id),
                message_id=assistant_message_id,
                query=query,
                report=report,
            )
            await asyncio.to_thread(
                chat_store.attach_run_id,
                message_id=assistant_message_id,
                user_id=int(current_user.id),
                run_id=run_doc["run_id"],
            )
            draft_message["run_id"] = run_doc["run_id"]

            # 分块流式传输回答内容
            for chunk in _chunk_text(answer):
                yield _format_sse(
                    "token",
                    {
                        "session_id": current_session_id,
                        "message_id": assistant_message_id,
                        "content": chunk,
                    },
                )
                await asyncio.sleep(0.01)  # 添加微小延迟以控制流速度

            # 发送消息完成事件
            yield _format_sse(
                "message_completed",
                {
                    "session_id": current_session_id,
                    "message": draft_message,
                    "report_summary": {
                        "status": report.get("status"),
                        "fail_reason": report.get("fail_reason"),
                        "citations": citations,
                    },
                },
            )
        except Exception as exc:
            # 发生错误时发送错误事件
            yield _format_sse(
                "error",
                {
                    "session_id": current_session_id,
                    "message": str(exc),
                },
            )

    # 返回流式响应
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

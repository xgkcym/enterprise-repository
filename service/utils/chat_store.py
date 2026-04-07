from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pymongo import DESCENDING

from src.database.mongodb import mongodb_client


CHAT_SESSIONS_COLLECTION = "chat_sessions"
CHAT_MESSAGES_COLLECTION = "chat_messages"
CHAT_MESSAGE_RUNS_COLLECTION = "chat_message_runs"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trim_text(value: str, *, max_len: int) -> str:
    text = (value or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


class ChatStore:
    def __init__(self) -> None:
        self.sessions = mongodb_client.get_collection(CHAT_SESSIONS_COLLECTION)
        self.messages = mongodb_client.get_collection(CHAT_MESSAGES_COLLECTION)
        self.message_runs = mongodb_client.get_collection(CHAT_MESSAGE_RUNS_COLLECTION)
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self.sessions.create_index([("user_id", 1), ("updated_at", DESCENDING)])
        self.sessions.create_index("session_id", unique=True)
        self.messages.create_index([("session_id", 1), ("created_at", 1)])
        self.messages.create_index("message_id", unique=True)
        self.message_runs.create_index("run_id", unique=True)
        self.message_runs.create_index([("session_id", 1), ("created_at", DESCENDING)])

    @staticmethod
    def _serialize_session(doc: dict[str, Any] | None) -> dict[str, Any] | None:
        if not doc:
            return None
        return {
            "session_id": doc["session_id"],
            "user_id": doc["user_id"],
            "title": doc.get("title", ""),
            "preview": doc.get("preview", ""),
            "message_count": doc.get("message_count", 0),
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
            "last_message_at": doc.get("last_message_at"),
            "deleted": bool(doc.get("deleted", False)),
        }

    @staticmethod
    def _serialize_message(doc: dict[str, Any] | None) -> dict[str, Any] | None:
        if not doc:
            return None
        return {
            "message_id": doc["message_id"],
            "session_id": doc["session_id"],
            "user_id": doc["user_id"],
            "role": doc["role"],
            "content": doc.get("content", ""),
            "citations": doc.get("citations", []),
            "status": doc.get("status", "completed"),
            "created_at": doc.get("created_at"),
            "run_id": doc.get("run_id"),
        }

    def create_session(self, *, user_id: int, first_query: str) -> dict[str, Any]:
        now = _utc_now()
        title = _trim_text(first_query, max_len=40) or "新会话"
        doc = {
            "session_id": str(uuid4()),
            "user_id": user_id,
            "title": title,
            "preview": _trim_text(first_query, max_len=80),
            "message_count": 0,
            "created_at": now,
            "updated_at": now,
            "last_message_at": now,
            "deleted": False,
        }
        self.sessions.insert_one(doc)
        return self._serialize_session(doc)

    def get_session(self, *, session_id: str, user_id: int, include_deleted: bool = False) -> dict[str, Any] | None:
        query: dict[str, Any] = {"session_id": session_id, "user_id": user_id}
        if not include_deleted:
            query["deleted"] = {"$ne": True}
        return self._serialize_session(self.sessions.find_one(query))

    def list_sessions(self, *, user_id: int) -> list[dict[str, Any]]:
        docs = self.sessions.find(
            {"user_id": user_id, "deleted": {"$ne": True}},
            sort=[("updated_at", DESCENDING)],
        )
        return [self._serialize_session(doc) for doc in docs]

    def create_message(
        self,
        *,
        session_id: str,
        user_id: int,
        role: str,
        content: str,
        citations: list[str] | None = None,
        run_id: str | None = None,
        status: str = "completed",
        message_id: str | None = None,
    ) -> dict[str, Any]:
        now = _utc_now()
        doc = {
            "message_id": message_id or str(uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content or "",
            "citations": citations or [],
            "status": status,
            "created_at": now,
            "run_id": run_id,
        }
        self.messages.insert_one(doc)
        self.sessions.update_one(
            {"session_id": session_id, "user_id": user_id},
            {
                "$set": {
                    "updated_at": now,
                    "last_message_at": now,
                    "preview": _trim_text(content or "", max_len=80),
                },
                "$inc": {"message_count": 1},
            },
        )
        return self._serialize_message(doc)

    def list_messages(self, *, session_id: str, user_id: int) -> list[dict[str, Any]]:
        docs = self.messages.find(
            {"session_id": session_id, "user_id": user_id},
            sort=[("created_at", 1)],
        )
        return [self._serialize_message(doc) for doc in docs]

    def create_run(
        self,
        *,
        session_id: str,
        user_id: int,
        message_id: str,
        query: str,
        report: dict[str, Any],
    ) -> dict[str, Any]:
        doc = {
            "run_id": str(uuid4()),
            "session_id": session_id,
            "user_id": user_id,
            "message_id": message_id,
            "query": query,
            "report": report,
            "created_at": _utc_now(),
        }
        self.message_runs.insert_one(doc)
        return {"run_id": doc["run_id"], "created_at": doc["created_at"]}

    def attach_run_id(self, *, message_id: str, user_id: int, run_id: str) -> None:
        self.messages.update_one(
            {"message_id": message_id, "user_id": user_id},
            {"$set": {"run_id": run_id}},
        )

    def soft_delete_session(self, *, session_id: str, user_id: int) -> bool:
        now = _utc_now()
        result = self.sessions.update_one(
            {"session_id": session_id, "user_id": user_id, "deleted": {"$ne": True}},
            {"$set": {"deleted": True, "updated_at": now}},
        )
        return result.modified_count > 0


chat_store = ChatStore()

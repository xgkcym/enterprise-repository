from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import Depends, Query

from service.dependencies.auth import get_current_active_user
from service.models.users import UserModel
from service.router.agent.index import agent_router
from service.utils.chat_store import chat_store


LOCAL_TZ = ZoneInfo("Asia/Shanghai")


def _parse_created_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _safe_number(value: Any, default: int | float = 0) -> int | float:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_daily_bucket(days: int = 7) -> dict[str, dict[str, Any]]:
    today = datetime.now(LOCAL_TZ).date()
    buckets: dict[str, dict[str, Any]] = {}
    for offset in range(days - 1, -1, -1):
        current = today - timedelta(days=offset)
        key = current.isoformat()
        buckets[key] = {
            "date": key,
            "request_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
    return buckets


def _build_action_metrics(action_stats: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    rows = []
    for action, stats in action_stats.items():
        count = int(stats["count"])
        success = int(stats["success"])
        failed = int(stats["failed"])
        rows.append(
            {
                "action": action,
                "count": count,
                "success_rate": round(success / count, 4) if count else 0,
                "fail_rate": round(failed / count, 4) if count else 0,
                "avg_duration_ms": int(stats["duration_ms"] / count) if count else 0,
                "avg_total_tokens": int(stats["total_tokens"] / count) if count else 0,
                "avg_estimated_cost_usd": round(stats["estimated_cost_usd"] / count, 6) if count else 0,
            }
        )
    return sorted(rows, key=lambda item: item["count"], reverse=True)


def _build_rank_rows(metric_map: dict[str, dict[str, float]], *, key_name: str) -> list[dict[str, Any]]:
    rows = []
    for key, stats in metric_map.items():
        count = int(stats["count"])
        failed = int(stats["failed"])
        rows.append(
            {
                key_name: key,
                "count": count,
                "total_tokens": int(stats["total_tokens"]),
                "estimated_cost_usd": round(stats["estimated_cost_usd"], 6),
                "avg_duration_ms": int(stats["duration_ms"] / count) if count else 0,
                "fail_rate": round(failed / count, 4) if count else 0,
            }
        )
    return sorted(rows, key=lambda item: (item["count"], item["total_tokens"]), reverse=True)


def _summarize_overview(runs: list[dict[str, Any]], sessions: list[dict[str, Any]]) -> dict[str, Any]:
    today_start = datetime.now(LOCAL_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    buckets = _build_daily_bucket(7)

    today_request_count = 0
    today_total_tokens = 0
    today_estimated_cost = 0.0
    today_duration_sum = 0
    today_duration_count = 0
    today_failed_count = 0
    today_session_ids: set[str] = set()
    today_user_ids: set[str] = set()
    action_distribution: dict[str, int] = {}
    model_distribution: dict[str, int] = {}
    fail_reason_distribution: dict[str, int] = {}
    action_stats: dict[str, dict[str, float]] = {}
    user_stats: dict[str, dict[str, float]] = {}
    session_stats: dict[str, dict[str, float]] = {}

    for doc in runs:
        created_at = _parse_created_at(doc.get("created_at"))
        if not created_at:
            continue

        local_dt = created_at.astimezone(LOCAL_TZ)
        day_key = local_dt.date().isoformat()
        report = doc.get("report") or {}
        llm_usage = report.get("llm_usage") or {}
        total_tokens = int(_safe_number(llm_usage.get("total_tokens"), 0))
        estimated_cost = float(_safe_number(llm_usage.get("estimated_cost_usd"), 0.0))
        duration_ms = int(_safe_number(report.get("duration_ms"), 0))
        status = report.get("status") or "pending"
        action = report.get("action") or "unknown"
        user_key = str(doc.get("user_id") or "unknown")
        session_key = str(doc.get("session_id") or "unknown")
        fail_reason = (report.get("fail_reason") or "").strip()

        if day_key in buckets:
            bucket = buckets[day_key]
            bucket["request_count"] += 1
            bucket["total_tokens"] += total_tokens
            bucket["estimated_cost_usd"] = round(bucket["estimated_cost_usd"] + estimated_cost, 6)
            if status == "failed":
                bucket["failed_count"] += 1
            elif status == "success":
                bucket["success_count"] += 1

        action_distribution[action] = action_distribution.get(action, 0) + 1
        if fail_reason:
            fail_reason_distribution[fail_reason] = fail_reason_distribution.get(fail_reason, 0) + 1
        for model in llm_usage.get("models") or []:
            model_distribution[model] = model_distribution.get(model, 0) + 1

        action_bucket = action_stats.setdefault(
            action,
            {"count": 0, "success": 0, "failed": 0, "duration_ms": 0, "total_tokens": 0, "estimated_cost_usd": 0.0},
        )
        action_bucket["count"] += 1
        action_bucket["duration_ms"] += duration_ms
        action_bucket["total_tokens"] += total_tokens
        action_bucket["estimated_cost_usd"] += estimated_cost
        if status == "success":
            action_bucket["success"] += 1
        elif status == "failed":
            action_bucket["failed"] += 1

        for metric_map, key in ((user_stats, user_key), (session_stats, session_key)):
            bucket = metric_map.setdefault(
                key,
                {"count": 0, "failed": 0, "duration_ms": 0, "total_tokens": 0, "estimated_cost_usd": 0.0},
            )
            bucket["count"] += 1
            bucket["duration_ms"] += duration_ms
            bucket["total_tokens"] += total_tokens
            bucket["estimated_cost_usd"] += estimated_cost
            if status == "failed":
                bucket["failed"] += 1

        if local_dt >= today_start:
            today_request_count += 1
            today_total_tokens += total_tokens
            today_estimated_cost += estimated_cost
            if session_key and session_key != "unknown":
                today_session_ids.add(session_key)
            if user_key and user_key != "unknown":
                today_user_ids.add(user_key)
            if duration_ms > 0:
                today_duration_sum += duration_ms
                today_duration_count += 1
            if status == "failed":
                today_failed_count += 1

    avg_duration_ms = int(today_duration_sum / today_duration_count) if today_duration_count else 0
    avg_tokens_per_request = int(today_total_tokens / today_request_count) if today_request_count else 0
    fail_rate = round(today_failed_count / today_request_count, 4) if today_request_count else 0
    today_new_session_count = 0
    avg_session_message_count = 0
    max_session_message_count = 0
    if sessions:
        today_new_session_count = len(sessions)
        message_counts = [int(_safe_number(item.get("message_count"), 0)) for item in sessions]
        avg_session_message_count = int(sum(message_counts) / len(message_counts)) if message_counts else 0
        max_session_message_count = max(message_counts) if message_counts else 0

    return {
        "overview": {
            "today_request_count": today_request_count,
            "today_active_users": len(today_user_ids),
            "today_active_sessions": len({item for item in today_session_ids if item}),
            "today_new_sessions": today_new_session_count,
            "today_total_tokens": today_total_tokens,
            "today_estimated_cost_usd": round(today_estimated_cost, 6),
            "avg_duration_ms": avg_duration_ms,
            "avg_tokens_per_request": avg_tokens_per_request,
            "avg_session_message_count": avg_session_message_count,
            "max_session_message_count": max_session_message_count,
            "fail_rate": fail_rate,
        },
        "daily_trend": list(buckets.values()),
        "action_distribution": [
            {"action": action, "count": count}
            for action, count in sorted(action_distribution.items(), key=lambda item: item[1], reverse=True)
        ],
        "model_distribution": [
            {"model": model, "count": count}
            for model, count in sorted(model_distribution.items(), key=lambda item: item[1], reverse=True)
        ],
        "fail_reason_distribution": [
            {"fail_reason": reason, "count": count}
            for reason, count in sorted(fail_reason_distribution.items(), key=lambda item: item[1], reverse=True)
        ],
        "action_metrics": _build_action_metrics(action_stats),
        "top_users": _build_rank_rows(user_stats, key_name="user_id")[:10],
        "top_sessions": _build_rank_rows(session_stats, key_name="session_id")[:10],
    }


def _serialize_run(doc: dict[str, Any]) -> dict[str, Any]:
    report = doc.get("report") or {}
    llm_usage = report.get("llm_usage") or {}
    answer = (report.get("answer") or "").strip()
    return {
        "run_id": doc.get("run_id"),
        "session_id": doc.get("session_id"),
        "user_id": doc.get("user_id"),
        "message_id": doc.get("message_id"),
        "created_at": doc.get("created_at"),
        "query": doc.get("query") or report.get("query") or "",
        "resolved_query": report.get("resolved_query") or "",
        "working_query": report.get("working_query") or "",
        "action": report.get("action") or "",
        "status": report.get("status") or "",
        "reason": report.get("reason") or "",
        "fail_reason": report.get("fail_reason") or "",
        "answer_preview": answer[:160],
        "citations": report.get("citations") or [],
        "duration_ms": int(_safe_number(report.get("duration_ms"), 0)),
        "current_step": int(_safe_number(report.get("current_step"), 0)),
        "max_steps": int(_safe_number(report.get("max_steps"), 0)),
        "prompt_tokens": int(_safe_number(llm_usage.get("prompt_tokens"), 0)),
        "completion_tokens": int(_safe_number(llm_usage.get("completion_tokens"), 0)),
        "total_tokens": int(_safe_number(llm_usage.get("total_tokens"), 0)),
        "llm_call_count": int(_safe_number(llm_usage.get("call_count"), 0)),
        "estimated_cost_usd": float(_safe_number(llm_usage.get("estimated_cost_usd"), 0.0)),
        "models": llm_usage.get("models") or [],
        "rewrite_query": report.get("rewrite_query") or "",
        "expand_query": report.get("expand_query") or [],
        "decompose_query": report.get("decompose_query") or [],
        "trace": report.get("trace") or [],
        "action_history": report.get("action_history") or [],
    }


@agent_router.get("/admin/monitor/overview")
async def get_agent_monitor_overview(
    current_user: UserModel = Depends(get_current_active_user),
):
    _ = current_user
    start = datetime.now(LOCAL_TZ).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6)
    start_at = start.astimezone(timezone.utc).isoformat()
    runs, sessions = await asyncio.gather(
        asyncio.to_thread(chat_store.list_runs_since, start_at=start_at),
        asyncio.to_thread(chat_store.list_sessions_since, start_at=start_at),
    )
    data = _summarize_overview(runs, sessions)
    return {"code": 200, "message": "success", "data": data}


@agent_router.get("/admin/monitor/runs")
async def get_agent_monitor_runs(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: UserModel = Depends(get_current_active_user),
):
    _ = current_user
    runs = await asyncio.to_thread(chat_store.list_recent_runs, limit=limit)
    data = [_serialize_run(doc) for doc in runs]
    return {"code": 200, "message": "success", "data": data}

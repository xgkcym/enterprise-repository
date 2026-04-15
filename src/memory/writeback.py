from __future__ import annotations

import hashlib
import re

from core.settings import settings
from src.memory import memory_service
from src.types.memory_type import MemoryWriteCandidate, MemoryWriteRequest, MemoryWriteResult


EXPLICIT_MEMORY_PREFIXES = (
    "\u8bb0\u4f4f",
    "\u8bf7\u8bb0\u4f4f",
    "\u5e2e\u6211\u8bb0\u4f4f",
    "\u4f60\u8bb0\u4e00\u4e0b",
    "\u8bb0\u4e00\u4e0b",
    "remember that",
    "please remember",
)


PREFERENCE_RULES = [
    (
        r"(\u4ee5\u540e|\u4eca\u540e|\u9ed8\u8ba4|by default|from now on).*(\u8be6\u7ec6|\u8be6\u7ec6\u4e00\u70b9|\u66f4\u8be6\u7ec6|detailed|more detailed)",
        "preference",
        "\u7528\u6237\u504f\u597d\u66f4\u8be6\u7ec6\u7684\u56de\u7b54",
        ["answer_style", "detailed"],
    ),
    (
        r"(\u4ee5\u540e|\u4eca\u540e|\u9ed8\u8ba4|by default|from now on).*(\u7b80\u6d01|\u7b80\u77ed|\u7cbe\u7b80|concise|brief)",
        "preference",
        "\u7528\u6237\u504f\u597d\u66f4\u7b80\u6d01\u7684\u56de\u7b54",
        ["answer_style", "concise"],
    ),
    (
        r"(\u4ee5\u540e|\u4eca\u540e|\u9ed8\u8ba4|by default|from now on).*(\u4e2d\u6587|\u4f7f\u7528\u4e2d\u6587|in chinese|speak chinese)",
        "constraint",
        "\u9ed8\u8ba4\u4f7f\u7528\u4e2d\u6587\u56de\u7b54",
        ["language", "zh-CN"],
    ),
    (
        r"(\u4ee5\u540e|\u4eca\u540e|\u9ed8\u8ba4|by default|from now on).*(\u82f1\u6587|in english|english)",
        "constraint",
        "\u9ed8\u8ba4\u4f7f\u7528\u82f1\u6587\u56de\u7b54",
        ["language", "en"],
    ),
    (
        r"(\u4e0d\u8981|\u522b|disable|do not use|don't use).*(\u8054\u7f51|web search|web\u641c\u7d22)",
        "constraint",
        "\u9ed8\u8ba4\u4e0d\u8981\u4f7f\u7528\u8054\u7f51\u641c\u7d22",
        ["web_search", "disabled"],
    ),
]


def _normalize_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def _build_dedupe_key(memory_type: str, content: str) -> str:
    normalized = _normalize_text(content).lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"{memory_type}:{digest}"


def _extract_explicit_memory_content(query: str) -> str:
    normalized = _normalize_text(query)
    lowered = normalized.lower()
    for prefix in EXPLICIT_MEMORY_PREFIXES:
        lowered_prefix = prefix.lower()
        if lowered.startswith(lowered_prefix):
            return normalized[len(prefix) :].strip(" :\uff1a\uff0c,\u3002")
    return ""


def _extract_candidates(request: MemoryWriteRequest) -> list[MemoryWriteCandidate]:
    query = _normalize_text(request.query)
    if not query:
        return []

    candidates: list[MemoryWriteCandidate] = []

    explicit_content = _extract_explicit_memory_content(query)
    if explicit_content:
        candidates.append(
            MemoryWriteCandidate(
                memory_type="task_context",
                scope="user",
                content=explicit_content,
                summary=explicit_content,
                tags=["explicit_memory"],
                importance=0.9,
                confidence=0.95,
                source="user_explicit",
                dedupe_key=_build_dedupe_key("task_context", explicit_content),
            )
        )

    for pattern, memory_type, summary, tags in PREFERENCE_RULES:
        if not re.search(pattern, query, flags=re.IGNORECASE):
            continue
        candidates.append(
            MemoryWriteCandidate(
                memory_type=memory_type,
                scope="user",
                content=summary,
                summary=summary,
                tags=tags,
                importance=0.85,
                confidence=0.9,
                source="user_explicit",
                dedupe_key=_build_dedupe_key(memory_type, summary),
            )
        )

    unique_candidates: list[MemoryWriteCandidate] = []
    seen = set()
    for candidate in candidates:
        if candidate.dedupe_key in seen:
            continue
        seen.add(candidate.dedupe_key)
        unique_candidates.append(candidate)
    return unique_candidates


def write_long_term_memory(request: MemoryWriteRequest) -> MemoryWriteResult:
    if not settings.memory_enabled or not settings.memory_write_enabled:
        return MemoryWriteResult(
            success=True,
            message="memory write skipped",
            diagnostics=["memory_write_disabled"],
        )

    if not request.user_id:
        return MemoryWriteResult(
            success=True,
            message="memory write skipped",
            diagnostics=["memory_write_skipped_missing_user_id"],
        )

    if not memory_service.store.is_available():
        diagnostics = ["memory_store_unavailable_for_write"]
        import_error = getattr(memory_service.store, "import_error", None)
        if import_error:
            diagnostics.append(f"memory_store_import_error={import_error}")
        return MemoryWriteResult(
            success=True,
            message="memory write skipped",
            diagnostics=diagnostics,
        )

    candidates = _extract_candidates(request)
    if not candidates:
        return MemoryWriteResult(
            success=True,
            message="memory write skipped",
            diagnostics=["memory_write_no_candidates"],
        )

    written_count = 0
    skipped_count = 0
    records_to_write = []

    for candidate in candidates:
        if candidate.importance < settings.memory_write_min_importance:
            skipped_count += 1
            continue

        existing = memory_service.store.get_by_dedupe_key(
            user_id=request.user_id,
            dedupe_key=candidate.dedupe_key,
        )

        record = memory_service.build_record(
            memory_id=existing.memory_id if existing else None,
            user_id=request.user_id,
            session_id=request.session_id,
            memory_type=candidate.memory_type,
            scope=candidate.scope,
            content=candidate.content,
            summary=candidate.summary,
            tags=candidate.tags,
            importance=candidate.importance,
            confidence=candidate.confidence,
            source=candidate.source,
            dedupe_key=candidate.dedupe_key,
            created_at=existing.created_at if existing else None,
            expires_at=candidate.expires_at,
            metadata=candidate.metadata,
        )
        records_to_write.append(record)

    memory_ids = memory_service.save_records(records_to_write)
    written_count = len(memory_ids)

    diagnostics = [f"memory_write_candidates={len(candidates)}", f"memory_write_written={written_count}"]
    if skipped_count:
        diagnostics.append(f"memory_write_skipped={skipped_count}")

    return MemoryWriteResult(
        success=True,
        message="memory write completed",
        written_count=written_count,
        skipped_count=skipped_count,
        memory_ids=memory_ids,
        candidates=candidates,
        diagnostics=diagnostics,
    )

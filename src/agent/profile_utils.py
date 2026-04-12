from typing import Any, Iterable


TOPIC_PROFILE_KEYS = ("preferred_topics", "topics", "topic_hints")


def _raw_topics(profile_or_topics: dict[str, Any] | Iterable[str] | str | None):
    if profile_or_topics is None:
        return []

    if isinstance(profile_or_topics, dict):
        for key in TOPIC_PROFILE_KEYS:
            if key in profile_or_topics:
                return profile_or_topics.get(key)
        return []

    return profile_or_topics


def extract_preferred_topics(
    profile_or_topics: dict[str, Any] | Iterable[str] | str | None,
    *,
    limit: int = 5,
) -> list[str]:
    raw_topics = _raw_topics(profile_or_topics)
    if isinstance(raw_topics, str):
        raw_topics = [raw_topics]
    if not isinstance(raw_topics, (list, tuple, set)):
        return []

    topics: list[str] = []
    seen: set[str] = set()
    for item in raw_topics:
        if not isinstance(item, str):
            continue
        normalized = item.strip()
        marker = normalized.lower()
        if not normalized or marker in seen:
            continue
        seen.add(marker)
        topics.append(normalized)
        if len(topics) >= limit:
            break
    return topics


def build_preferred_topics_note(
    profile_or_topics: dict[str, Any] | Iterable[str] | str | None,
) -> str:
    topics = extract_preferred_topics(profile_or_topics)
    if not topics:
        return ""

    return (
        "User preference hints:\n"
        f"- preferred_topics: {', '.join(topics)}\n"
        "- Use these only as weak hints when they help clarify context, create retrieval variants, or provide relevant examples.\n"
        "- Do not override the user's current question or introduce unrelated topics."
    )


def build_topic_guidance_queries(
    base_query: str,
    profile_or_topics: dict[str, Any] | Iterable[str] | str | None,
    *,
    max_queries: int = 2,
) -> list[str]:
    normalized_query = (base_query or "").strip()
    if not normalized_query:
        return []

    topics = extract_preferred_topics(profile_or_topics)
    if not topics:
        return []

    query_lower = normalized_query.lower()
    result: list[str] = []
    seen: set[str] = {query_lower}
    for topic in topics:
        if topic.lower() in query_lower:
            continue
        candidate = f"{normalized_query} {topic}".strip()
        marker = candidate.lower()
        if marker in seen:
            continue
        seen.add(marker)
        result.append(candidate)
        if len(result) >= max_queries:
            break

    return result


def merge_queries_with_topic_guidance(
    queries: list[str] | None,
    base_query: str,
    profile_or_topics: dict[str, Any] | Iterable[str] | str | None,
    *,
    limit: int = 3,
    max_topic_queries: int = 1,
) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for item in list(queries or []) + build_topic_guidance_queries(
        base_query,
        profile_or_topics,
        max_queries=max_topic_queries,
    ):
        candidate = (item or "").strip()
        marker = candidate.lower()
        if not candidate or marker in seen:
            continue
        seen.add(marker)
        merged.append(candidate)
        if len(merged) >= limit:
            break

    if not merged and (base_query or "").strip():
        merged.append(base_query.strip())
    return merged

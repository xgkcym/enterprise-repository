import time
from typing import Optional, TypeVar

from src.types.base_type import BaseResult
from src.types.event_type import BaseEvent
from utils.utils import get_current_time


TEvent = TypeVar("TEvent", bound=BaseEvent)


def create_event(event_cls, name: str, input_data=None, max_attempt: int = 3):
    return event_cls(
        name=name,
        input=input_data,
        max_attempt=max_attempt,
        started_at=get_current_time(),
    )


def get_next_attempt(action_history: list[BaseEvent], event_name: str) -> int:
    last_event = next((event for event in reversed(action_history) if event.name == event_name), None)
    if last_event:
        return last_event.attempt + 1
    return 1


def finalize_event(event: TEvent, result: Optional[BaseResult], start_time: float) -> TEvent:
    event.output = result
    event.status = "success" if result and result.success else "failed"
    event.error = result.error_detail if result else None
    event.ended_at = get_current_time()
    event.duration = int((time.time() - start_time) * 1000)
    return event

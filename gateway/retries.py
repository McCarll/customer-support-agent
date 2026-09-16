"""Exponential backoff for transient backend failures.

Timeouts and invalid parameters are not retried: the deadline has already
been exceeded, and bad input will fail again.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

from .store import RetryableBackendError

T = TypeVar("T")

RETRYABLE = (RetryableBackendError, ConnectionError)


def retry_with_backoff(
    operation: Callable[[], T],
    *,
    max_attempts: int = 4,
    base_delay_seconds: float = 0.05,
    max_delay_seconds: float = 1.0,
    jitter: bool = True,
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except RETRYABLE as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            delay = min(max_delay_seconds, base_delay_seconds * (2 ** (attempt - 1)))
            if jitter:
                delay = delay * (0.5 + random.random())
            time.sleep(delay)
    assert last_error is not None
    raise last_error

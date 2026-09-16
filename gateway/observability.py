"""Shared observability helpers for traces, spans, and structured logs.

In AgentCore Runtime, aws-opentelemetry-distro exports to CloudWatch / X-Ray.
Locally, spans are also written as JSONL so failures can be inspected without AWS.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

log = logging.getLogger("customer_support.observability")

_TRACE_DIR = Path(os.getenv("TRACE_DIR", ".local/traces"))


def _trace_file() -> Path:
    _TRACE_DIR.mkdir(parents=True, exist_ok=True)
    return _TRACE_DIR / "spans.jsonl"


def new_trace_id() -> str:
    return uuid.uuid4().hex


def emit_span(
    name: str,
    *,
    trace_id: str,
    status: str = "OK",
    attributes: dict[str, Any] | None = None,
    error: str | None = None,
    duration_ms: float | None = None,
    parent: str | None = None,
) -> dict[str, Any]:
    span = {
        "trace_id": trace_id,
        "span_id": uuid.uuid4().hex[:16],
        "parent_span_id": parent,
        "name": name,
        "status": status,
        "duration_ms": duration_ms,
        "attributes": attributes or {},
        "error": error,
        "ts": time.time(),
    }
    path = _trace_file()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(span) + "\n")
    if status == "ERROR":
        log.error("span=%s status=ERROR error=%s attrs=%s", name, error, attributes)
    else:
        log.info("span=%s status=%s attrs=%s", name, status, attributes)
    return span


@contextmanager
def span(
    name: str,
    *,
    trace_id: str,
    attributes: dict[str, Any] | None = None,
    parent: str | None = None,
) -> Iterator[dict[str, Any]]:
    started = time.perf_counter()
    current: dict[str, Any] = {
        "name": name,
        "attributes": dict(attributes or {}),
        "status": "OK",
        "error": None,
    }
    try:
        yield current
    except Exception as exc:
        current["status"] = "ERROR"
        current["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        emit_span(
            name,
            trace_id=trace_id,
            status=current["status"],
            attributes=current["attributes"],
            error=current["error"],
            duration_ms=(time.perf_counter() - started) * 1000,
            parent=parent,
        )

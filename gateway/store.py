"""Customer, order, and refund store with idempotent refunds."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("SUPPORT_DB", Path(__file__).resolve().parents[1] / ".local" / "support.db"))

_lock = threading.Lock()
_fail_remaining = 0


class RetryableBackendError(RuntimeError):
    """Transient backend failure that callers should retry."""


class ToolTimeoutError(TimeoutError):
    """Simulated or real tool timeout."""


class InvalidToolParameters(ValueError):
    """Caller sent parameters that cannot be processed."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def configure_failures(fail_times: int = 0) -> None:
    global _fail_remaining
    _fail_remaining = fail_times


def _maybe_inject_failure(tool_name: str) -> None:
    global _fail_remaining
    mode = os.getenv("FAILURE_MODE", "none")
    if mode == "timeout" and tool_name in {"get_order", "refund_customer"}:
        raise ToolTimeoutError(f"{tool_name} exceeded the Gateway timeout")
    if mode == "http_500" and tool_name == "refund_customer":
        raise RetryableBackendError("HTTP 500 from refund backend")
    if _fail_remaining > 0 and tool_name == "refund_customer":
        _fail_remaining -= 1
        raise RetryableBackendError("HTTP 500 from refund backend")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with _lock, connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                plan TEXT NOT NULL,
                country TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                product TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                delay_reason TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );
            CREATE TABLE IF NOT EXISTS refunds (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                order_id TEXT NOT NULL,
                amount REAL NOT NULL,
                reason TEXT NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.executemany(
            """
            INSERT OR IGNORE INTO customers (id, name, email, plan, country)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("CUST-001", "Alice Johnson", "alice@example.com", "gold", "IE"),
                ("CUST-002", "Bob Smith", "bob@example.com", "standard", "DE"),
                ("CUST-003", "Chen Wei", "chen@example.com", "gold", "FR"),
            ],
        )
        conn.executemany(
            """
            INSERT OR IGNORE INTO orders
                (id, customer_id, product, amount, status, delay_reason)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("123", "CUST-001", "Smart Watch", 249.99, "delayed", "Carrier backlog in Dublin"),
                ("456", "CUST-002", "USB-C Hub", 54.99, "delivered", None),
                ("789", "CUST-001", "Wireless Headphones", 79.99, "processing", None),
                ("1001", "CUST-003", "Mechanical Keyboard", 129.99, "shipped", None),
            ],
        )


def _fetch_order(order_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?", (str(order_id).strip(),)
        ).fetchone()
    return dict(row) if row else None


def get_order(order_id: str) -> dict[str, Any]:
    if not order_id or not str(order_id).strip():
        raise InvalidToolParameters("order_id is required")
    _maybe_inject_failure("get_order")
    row = _fetch_order(order_id)
    if not row:
        return {"found": False, "order_id": order_id}
    return {"found": True, "order": row}


def get_customer(customer_id: str) -> dict[str, Any]:
    if not customer_id or not str(customer_id).strip():
        raise InvalidToolParameters("customer_id is required")
    _maybe_inject_failure("get_customer")
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM customers WHERE id = ?", (str(customer_id).strip(),)
        ).fetchone()
    if not row:
        return {"found": False, "customer_id": customer_id}
    return {"found": True, "customer": dict(row)}


def refund_count() -> int:
    with connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM refunds").fetchone()
    return int(row["n"])


def get_refund_by_key(idempotency_key: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM refunds WHERE idempotency_key = ?", (idempotency_key,)
        ).fetchone()
    return dict(row) if row else None


def refund_customer(
    customer_id: str,
    amount: float,
    order_id: str,
    idempotency_key: str,
    reason: str = "",
) -> dict[str, Any]:
    if not customer_id:
        raise InvalidToolParameters("customer_id is required")
    if not order_id:
        raise InvalidToolParameters("order_id is required")
    if not idempotency_key:
        raise InvalidToolParameters("idempotency_key is required")
    try:
        amount_value = float(amount)
    except (TypeError, ValueError) as exc:
        raise InvalidToolParameters("amount must be a number") from exc
    if amount_value <= 0:
        raise InvalidToolParameters("amount must be greater than 0")

    _maybe_inject_failure("refund_customer")

    existing = get_refund_by_key(idempotency_key)
    if existing:
        return {"replayed": True, "refund": existing}

    order = _fetch_order(order_id)
    if not order:
        raise InvalidToolParameters(f"order '{order_id}' does not exist")
    if order["customer_id"] != customer_id:
        raise InvalidToolParameters("order does not belong to this customer")

    refund = {
        "id": f"REF-{uuid.uuid4().hex[:8]}",
        "customer_id": customer_id,
        "order_id": order_id,
        "amount": amount_value,
        "reason": reason or "customer request",
        "idempotency_key": idempotency_key,
        "status": "processed",
        "created_at": _now(),
    }
    with _lock, connect() as conn:
        existing = conn.execute(
            "SELECT * FROM refunds WHERE idempotency_key = ?", (idempotency_key,)
        ).fetchone()
        if existing:
            return {"replayed": True, "refund": dict(existing)}
        conn.execute(
            """
            INSERT INTO refunds
                (id, customer_id, order_id, amount, reason, idempotency_key, status, created_at)
            VALUES (:id, :customer_id, :order_id, :amount, :reason, :idempotency_key, :status, :created_at)
            """,
            refund,
        )
    return {"replayed": False, "refund": refund}


def dump_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, default=str)


def reset_for_tests(tmp_path: Path) -> None:
    global DB_PATH, _fail_remaining
    DB_PATH = tmp_path / "support.db"
    _fail_remaining = 0
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    time.sleep(0)

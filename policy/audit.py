"""Audit trail — append-only logging of all actions."""
from datetime import datetime, timezone
from db import get_connection


def log_audit_event(
    exception_id: str,
    action: str,
    agent: str | None = None,
    original_value: str | None = None,
    proposed_value: str | None = None,
    confidence: float | None = None,
    reasoning: str | None = None,
    policy_applied: str | None = None,
) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO audit_events
        (exception_id, action, agent, original_value, proposed_value, confidence, reasoning, policy_applied, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            exception_id, action, agent, original_value, proposed_value,
            confidence, reasoning, policy_applied,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return event_id


def get_audit_trail(exception_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM audit_events WHERE exception_id = ? ORDER BY timestamp",
        (exception_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

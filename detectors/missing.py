"""Detect missing submissions based on expected reporting cadence."""
from db import get_connection


def detect_missing_data(
    expected_period: str,
    supplier_id: str | None = None,
) -> list[dict]:
    conn = get_connection()

    if supplier_id:
        suppliers = conn.execute(
            "SELECT id, name FROM suppliers WHERE id = ?", (supplier_id,)
        ).fetchall()
    else:
        suppliers = conn.execute("SELECT id, name FROM suppliers").fetchall()

    exceptions = []
    for supplier in suppliers:
        has_history = conn.execute(
            """SELECT COUNT(*) as cnt FROM activity_records
            WHERE supplier_id = ? AND source = 'supplier_submission'""",
            (supplier["id"],),
        ).fetchone()

        if has_history["cnt"] == 0:
            continue

        current = conn.execute(
            """SELECT COUNT(*) as cnt FROM activity_records
            WHERE supplier_id = ? AND reporting_period = ? AND source = 'supplier_submission'""",
            (supplier["id"], expected_period),
        ).fetchone()

        if current["cnt"] == 0:
            last = conn.execute(
                """SELECT reporting_period FROM activity_records
                WHERE supplier_id = ? AND source = 'supplier_submission'
                ORDER BY reporting_period DESC LIMIT 1""",
                (supplier["id"],),
            ).fetchone()

            exceptions.append({
                "supplier_id": supplier["id"],
                "supplier_name": supplier["name"],
                "exception_type": "missing_data",
                "severity": "medium",
                "expected_period": expected_period,
                "last_submission_period": last["reporting_period"] if last else None,
            })

    conn.close()
    return exceptions

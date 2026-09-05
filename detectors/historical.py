"""Detect when a submitted value deviates significantly from historical baseline."""
import statistics
from db import get_connection


def detect_historical_deviation(
    supplier_id: str,
    facility_id: str,
    activity_type: str,
    current_period: str,
    threshold_pct: float = 0.30,
) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT quantity FROM activity_records
        WHERE supplier_id = ? AND facility_id = ? AND activity_type = ?
          AND reporting_period < ? AND source = 'supplier_submission'
        ORDER BY reporting_period DESC LIMIT 12""",
        (supplier_id, facility_id, activity_type, current_period),
    ).fetchall()

    if len(rows) < 3:
        return []

    historical_values = [r["quantity"] for r in rows]
    mean_val = statistics.mean(historical_values)
    stdev_val = statistics.stdev(historical_values) if len(historical_values) > 1 else 0

    current = conn.execute(
        """SELECT id, quantity FROM activity_records
        WHERE supplier_id = ? AND facility_id = ? AND activity_type = ?
          AND reporting_period = ? AND source = 'supplier_submission'""",
        (supplier_id, facility_id, activity_type, current_period),
    ).fetchone()
    conn.close()

    if not current:
        return []

    deviation_pct = abs(current["quantity"] - mean_val) / mean_val if mean_val else 0

    if deviation_pct > threshold_pct:
        return [{
            "record_id": current["id"],
            "exception_type": "historical_deviation",
            "severity": "high" if deviation_pct > 1.0 else "medium",
            "submitted_value": current["quantity"],
            "historical_mean": round(mean_val, 1),
            "historical_stdev": round(stdev_val, 1),
            "deviation_pct": round(deviation_pct * 100, 1),
        }]
    return []

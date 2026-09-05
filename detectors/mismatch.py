"""Detect discrepancies between different data sources for the same record."""
from db import get_connection


def detect_cross_source_mismatch(
    supplier_id: str,
    facility_id: str,
    activity_type: str,
    period: str,
    tolerance_pct: float = 0.05,
) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, quantity, source, raw_reference FROM activity_records
        WHERE supplier_id = ? AND facility_id = ? AND activity_type = ? AND reporting_period = ?""",
        (supplier_id, facility_id, activity_type, period),
    ).fetchall()
    conn.close()

    if len(rows) < 2:
        return []

    values_by_source = {r["source"]: {"quantity": r["quantity"], "record_id": r["id"]} for r in rows}
    quantities = [v["quantity"] for v in values_by_source.values()]
    unique_values = set(quantities)

    if len(unique_values) <= 1:
        return []

    min_val = min(quantities)
    max_val = max(quantities)
    spread_pct = (max_val - min_val) / min_val if min_val else 0

    if spread_pct <= tolerance_pct:
        return []

    source_summary = {src: data["quantity"] for src, data in values_by_source.items()}
    primary_record_id = values_by_source.get("supplier_submission", {}).get(
        "record_id", rows[0]["id"]
    )

    agreeing_groups: dict[float, list[str]] = {}
    for src, data in values_by_source.items():
        matched = False
        for val in agreeing_groups:
            if abs(data["quantity"] - val) / max(val, 1) <= tolerance_pct:
                agreeing_groups[val].append(src)
                matched = True
                break
        if not matched:
            agreeing_groups[data["quantity"]] = [src]

    num_groups = len(agreeing_groups)

    return [{
        "record_id": primary_record_id,
        "exception_type": "cross_source_mismatch",
        "severity": "critical" if num_groups > 2 else "high",
        "sources": source_summary,
        "spread_pct": round(spread_pct * 100, 1),
        "num_conflicting_groups": num_groups,
    }]

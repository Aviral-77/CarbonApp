"""HistoryAgent — analyzes historical baseline and identifies patterns."""
import json
import statistics

from strands import Agent, tool

from db import get_connection
from config import BEDROCK_MODEL_ID


@tool
def get_historical_data(
    supplier_id: str, facility_id: str, activity_type: str, num_months: int = 12
) -> str:
    """Retrieve historical activity records for a supplier/facility.

    Args:
        supplier_id: The supplier identifier.
        facility_id: The facility identifier.
        activity_type: Type of activity (electricity, natural_gas, etc.).
        num_months: Number of past months to retrieve.
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT reporting_period, quantity, unit FROM activity_records
        WHERE supplier_id = ? AND facility_id = ? AND activity_type = ?
          AND source = 'supplier_submission'
        ORDER BY reporting_period DESC LIMIT ?""",
        (supplier_id, facility_id, activity_type, num_months),
    ).fetchall()
    conn.close()

    if not rows:
        return json.dumps({"error": "No historical data found"})

    values = [r["quantity"] for r in rows]
    result = {
        "records": [dict(r) for r in rows],
        "statistics": {
            "mean": round(statistics.mean(values), 1),
            "stdev": round(statistics.stdev(values), 1) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "count": len(values),
        },
    }
    return json.dumps(result)


@tool
def compute_deviation(submitted_value: float, historical_mean: float, historical_stdev: float) -> str:
    """Compute how far a submitted value deviates from the historical baseline.

    Args:
        submitted_value: The value that was submitted.
        historical_mean: The mean of historical values.
        historical_stdev: The standard deviation of historical values.
    """
    abs_deviation = abs(submitted_value - historical_mean)
    pct_deviation = (abs_deviation / historical_mean * 100) if historical_mean else 0
    z_score = (abs_deviation / historical_stdev) if historical_stdev else float("inf")

    return json.dumps({
        "submitted_value": submitted_value,
        "historical_mean": historical_mean,
        "absolute_deviation": round(abs_deviation, 1),
        "percent_deviation": round(pct_deviation, 1),
        "z_score": round(z_score, 2),
        "is_anomalous": z_score > 2.0 or pct_deviation > 30,
    })


SYSTEM_PROMPT = """You are a HistoryAgent specializing in carbon emissions data analysis.
Your job is to analyze historical patterns for a supplier/facility and determine
whether a submitted value is consistent with past behavior.

When investigating, you should:
1. Retrieve historical data for the supplier/facility
2. Compute the deviation of the current value from the baseline
3. Report your findings with specific numbers

Always be precise with numbers. Report the historical mean, standard deviation,
and the exact deviation percentage. State whether the value looks anomalous and
suggest what the correct value might be based on the pattern."""


def create_history_agent(callback_handler=None) -> Agent:
    kwargs = {
        "model": f"bedrock/{BEDROCK_MODEL_ID}",
        "system_prompt": SYSTEM_PROMPT,
        "tools": [get_historical_data, compute_deviation],
    }
    if callback_handler:
        kwargs["callback_handler"] = callback_handler
    return Agent(**kwargs)

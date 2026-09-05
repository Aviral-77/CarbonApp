"""ERPAgent — queries ERP system records for cross-referencing."""
import json

from strands import Agent, tool

from db import get_connection
from config import BEDROCK_MODEL_ID, BASE_DIR


@tool
def query_erp_record(supplier_id: str, facility_id: str, period: str) -> str:
    """Query the ERP system for a supplier's recorded data for a period.

    Args:
        supplier_id: The supplier identifier.
        facility_id: The facility identifier.
        period: Reporting period in YYYY-MM format.
    """
    conn = get_connection()
    row = conn.execute(
        """SELECT id, quantity, unit, raw_reference FROM activity_records
        WHERE supplier_id = ? AND facility_id = ? AND reporting_period = ? AND source = 'erp'""",
        (supplier_id, facility_id, period),
    ).fetchone()
    conn.close()

    if not row:
        return json.dumps({"found": False, "message": f"No ERP record for {supplier_id}/{facility_id} in {period}"})

    result = {
        "found": True,
        "record_id": row["id"],
        "quantity": row["quantity"],
        "unit": row["unit"],
        "raw_reference": row["raw_reference"],
    }

    if row["raw_reference"]:
        ref_path = BASE_DIR / row["raw_reference"]
        if ref_path.exists():
            try:
                result["erp_detail"] = json.loads(ref_path.read_text())
            except Exception:
                pass

    return json.dumps(result)


@tool
def query_meter_reading(facility_id: str, period: str) -> str:
    """Query smart meter readings for a facility.

    Args:
        facility_id: The facility identifier.
        period: Reporting period in YYYY-MM format.
    """
    conn = get_connection()
    row = conn.execute(
        """SELECT id, quantity, unit, raw_reference FROM activity_records
        WHERE facility_id = ? AND reporting_period = ? AND source = 'meter'""",
        (facility_id, period),
    ).fetchone()
    conn.close()

    if not row:
        return json.dumps({"found": False, "message": f"No meter reading for {facility_id} in {period}"})

    result = {
        "found": True,
        "record_id": row["id"],
        "quantity": row["quantity"],
        "unit": row["unit"],
    }

    if row["raw_reference"]:
        ref_path = BASE_DIR / row["raw_reference"]
        if ref_path.exists():
            try:
                result["meter_detail"] = json.loads(ref_path.read_text())
            except Exception:
                pass

    return json.dumps(result)


SYSTEM_PROMPT = """You are an ERPAgent specializing in retrieving and interpreting
enterprise resource planning (ERP) records and meter readings for carbon data verification.

When asked to investigate:
1. Query the ERP system for the relevant supplier/facility/period
2. Check for meter readings if available
3. Report exactly what the ERP and meter data shows

Report specific values with their sources. Never infer — only report what the systems contain."""


def create_erp_agent(callback_handler=None) -> Agent:
    kwargs = {
        "model": f"bedrock/{BEDROCK_MODEL_ID}",
        "system_prompt": SYSTEM_PROMPT,
        "tools": [query_erp_record, query_meter_reading],
    }
    if callback_handler:
        kwargs["callback_handler"] = callback_handler
    return Agent(**kwargs)

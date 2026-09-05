"""CommunicatorAgent — drafts supplier clarification requests (simulated, never actually sent)."""
import json
from datetime import datetime, timezone

from strands import Agent, tool

from db import get_connection
from config import BEDROCK_MODEL_ID


@tool
def draft_clarification_email(
    supplier_id: str,
    supplier_name: str,
    subject: str,
    body: str,
    requested_data: str,
    deadline_days: int,
) -> str:
    """Draft and log a supplier clarification email (simulated — never actually sent).

    Args:
        supplier_id: The supplier identifier.
        supplier_name: The supplier's name.
        subject: Email subject line.
        body: Full email body text.
        requested_data: What specific data is being requested.
        deadline_days: Number of business days given to respond.
    """
    conn = get_connection()
    supplier = conn.execute(
        "SELECT contact_email FROM suppliers WHERE id = ?", (supplier_id,)
    ).fetchone()
    conn.close()

    email_record = {
        "status": "simulated_send",
        "to": supplier.get("contact_email", "unknown") if supplier else "unknown",
        "supplier_id": supplier_id,
        "supplier_name": supplier_name,
        "subject": subject,
        "body": body,
        "requested_data": requested_data,
        "deadline_days": deadline_days,
        "drafted_at": datetime.now(timezone.utc).isoformat(),
        "note": "SIMULATED — this email was drafted but not actually sent",
    }
    return json.dumps(email_record, indent=2)


SYSTEM_PROMPT = """You are a CommunicatorAgent that drafts professional clarification
requests to suppliers when carbon emissions data is missing or unclear.

When drafting a clarification email:
1. Be professional and specific about what data is needed
2. Reference the exact reporting period and facility
3. Set a reasonable deadline (typically 5 business days)
4. Include context about why the data is needed (carbon reporting obligations)

IMPORTANT: All emails are SIMULATED — they are logged but never actually sent.
Make this clear in your output. The email should be realistic and professional
but will only be stored in the audit trail."""


def create_communicator_agent(callback_handler=None) -> Agent:
    kwargs = {
        "model": f"bedrock/{BEDROCK_MODEL_ID}",
        "system_prompt": SYSTEM_PROMPT,
        "tools": [draft_clarification_email],
    }
    if callback_handler:
        kwargs["callback_handler"] = callback_handler
    return Agent(**kwargs)

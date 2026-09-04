"""Orchestrator — the top-level agent that coordinates specialist agents."""
import json
from datetime import datetime, timezone

from strands import Agent, tool

from db import get_connection
from config import BEDROCK_MODEL_ID
from agents.history_agent import create_history_agent
from agents.document_agent import create_document_agent
from agents.erp_agent import create_erp_agent
from agents.reconciliation_agent import create_reconciliation_agent
from agents.communicator_agent import create_communicator_agent
from policy.engine import apply_policy
from policy.audit import log_audit_event


def _run_agent(agent: Agent, prompt: str) -> str:
    result = agent(prompt)
    return str(result)


@tool
def investigate_with_history_agent(
    supplier_id: str, facility_id: str, activity_type: str
) -> str:
    """Use the HistoryAgent to analyze historical baseline data.

    Args:
        supplier_id: The supplier to investigate.
        facility_id: The facility to investigate.
        activity_type: The type of activity (electricity, natural_gas, etc.).
    """
    agent = create_history_agent()
    return _run_agent(
        agent,
        f"Analyze the historical data for supplier {supplier_id}, facility {facility_id}, "
        f"activity type {activity_type}. Report the mean, standard deviation, and any anomalies.",
    )


@tool
def investigate_with_document_agent(file_paths: str) -> str:
    """Use the DocumentAgent to extract data from documents.

    Args:
        file_paths: Comma-separated list of file paths to investigate.
    """
    agent = create_document_agent()
    paths = [p.strip() for p in file_paths.split(",")]
    return _run_agent(
        agent,
        f"Read and extract the energy consumption data from these documents: {', '.join(paths)}. "
        f"Report exact quantities, units, and any relevant context from each document.",
    )


@tool
def investigate_with_erp_agent(
    supplier_id: str, facility_id: str, period: str
) -> str:
    """Use the ERPAgent to check ERP records and meter readings.

    Args:
        supplier_id: The supplier to look up.
        facility_id: The facility to look up.
        period: Reporting period (YYYY-MM).
    """
    agent = create_erp_agent()
    return _run_agent(
        agent,
        f"Query ERP records and meter readings for supplier {supplier_id}, "
        f"facility {facility_id}, period {period}. Report all values found.",
    )


@tool
def reconcile_evidence(
    exception_id: str,
    evidence_json: str,
) -> str:
    """Use the ReconciliationAgent to produce a structured recommendation.

    Args:
        exception_id: The exception being reconciled.
        evidence_json: JSON string summarizing all evidence gathered from other agents.
    """
    agent = create_reconciliation_agent()
    return _run_agent(
        agent,
        f"Reconcile the following evidence for exception {exception_id}:\n{evidence_json}\n\n"
        f"Produce a structured reconciliation with confidence score, proposed value, "
        f"and step-by-step reasoning.",
    )


@tool
def draft_supplier_clarification(
    supplier_id: str, supplier_name: str, reason: str, expected_period: str
) -> str:
    """Use the CommunicatorAgent to draft a supplier clarification request.

    Args:
        supplier_id: The supplier to contact.
        supplier_name: The supplier's name.
        reason: Why clarification is needed.
        expected_period: The period for which data is expected.
    """
    agent = create_communicator_agent()
    return _run_agent(
        agent,
        f"Draft a clarification email to {supplier_name} ({supplier_id}) regarding: {reason}. "
        f"The expected reporting period is {expected_period}.",
    )


@tool
def apply_resolution_policy(exception_id: str, reconciliation_json: str) -> str:
    """Apply the deterministic policy engine to decide auto-resolve vs escalate.

    Args:
        exception_id: The exception to resolve.
        reconciliation_json: JSON output from the ReconciliationAgent.
    """
    try:
        reconciliation = json.loads(reconciliation_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid reconciliation JSON"})

    decision = apply_policy(exception_id, reconciliation)
    log_audit_event(
        exception_id=exception_id,
        action=decision["action"],
        agent="policy_engine",
        confidence=decision.get("confidence"),
        reasoning=decision.get("reasoning"),
        policy_applied=decision.get("policy"),
        proposed_value=str(decision.get("proposed_value", "")),
    )

    conn = get_connection()
    if decision["action"] == "auto_resolve":
        conn.execute(
            "UPDATE exceptions SET status = 'auto_resolved', resolved_at = ?, resolved_by = 'system' WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), exception_id),
        )
    elif decision["action"] == "escalate":
        conn.execute(
            "UPDATE exceptions SET status = 'escalated' WHERE id = ?",
            (exception_id,),
        )
    elif decision["action"] == "request_clarification":
        conn.execute(
            "UPDATE exceptions SET status = 'waiting' WHERE id = ?",
            (exception_id,),
        )
    conn.commit()
    conn.close()

    return json.dumps(decision, indent=2)


@tool
def get_exception_details(exception_id: str) -> str:
    """Get full details about an exception including related records.

    Args:
        exception_id: The exception to look up.
    """
    conn = get_connection()
    exc = conn.execute("SELECT * FROM exceptions WHERE id = ?", (exception_id,)).fetchone()
    if not exc:
        conn.close()
        return json.dumps({"error": f"Exception {exception_id} not found"})

    result = dict(exc)

    if exc["record_id"]:
        record = conn.execute("SELECT * FROM activity_records WHERE id = ?", (exc["record_id"],)).fetchone()
        if record:
            result["primary_record"] = dict(record)

    related = conn.execute(
        """SELECT * FROM activity_records
        WHERE supplier_id = ? AND facility_id = (
            SELECT facility_id FROM activity_records WHERE id = ?
        ) AND reporting_period = (
            SELECT reporting_period FROM activity_records WHERE id = ?
        )""",
        (exc["supplier_id"], exc["record_id"] or "", exc["record_id"] or ""),
    ).fetchall()
    result["all_source_records"] = [dict(r) for r in related]

    supplier = conn.execute("SELECT * FROM suppliers WHERE id = ?", (exc["supplier_id"],)).fetchone()
    if supplier:
        result["supplier"] = dict(supplier)

    conn.close()
    return json.dumps(result, indent=2, default=str)


SYSTEM_PROMPT = """You are the CarbonOps Orchestrator — a multi-agent coordinator that
investigates carbon data exceptions by dispatching specialist agents.

You have access to these specialist agents as tools:
- HistoryAgent: Analyzes historical patterns and baselines
- DocumentAgent: Extracts data from invoices and documents
- ERPAgent: Queries ERP records and meter readings
- ReconciliationAgent: Produces structured reconciliation with confidence scoring
- CommunicatorAgent: Drafts supplier clarification requests

Your investigation workflow:
1. Get exception details to understand the problem
2. Dispatch appropriate specialist agents to gather evidence
3. Send all evidence to the ReconciliationAgent for structured output
4. Apply the resolution policy to decide: auto-resolve, escalate, or request clarification

RULES:
- Always gather evidence from at least 2 sources before reconciling
- For missing data exceptions, go straight to CommunicatorAgent after confirming the gap
- Never guess — if sources conflict and you can't determine the truth, escalate
- The policy engine makes the final resolve/escalate decision, not you
- Log your reasoning at each step"""


def create_orchestrator(callback_handler=None) -> Agent:
    kwargs = {
        "model": f"bedrock/{BEDROCK_MODEL_ID}",
        "system_prompt": SYSTEM_PROMPT,
        "tools": [
            get_exception_details,
            investigate_with_history_agent,
            investigate_with_document_agent,
            investigate_with_erp_agent,
            reconcile_evidence,
            draft_supplier_clarification,
            apply_resolution_policy,
        ],
    }
    if callback_handler:
        kwargs["callback_handler"] = callback_handler
    return Agent(**kwargs)


def investigate_exception(exception_id: str, callback_handler=None) -> str:
    orchestrator = create_orchestrator(callback_handler)
    result = orchestrator(
        f"Investigate exception {exception_id}. "
        f"Get the details, gather evidence from relevant sources, "
        f"reconcile the findings, and apply the resolution policy."
    )
    return str(result)

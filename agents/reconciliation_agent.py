"""ReconciliationAgent — produces structured reconciliation output with confidence scoring."""
import json

from strands import Agent, tool

from config import BEDROCK_MODEL_ID


@tool
def produce_reconciliation(
    exception_id: str,
    evidence_summary: str,
    sources_agreeing: str,
    sources_disagreeing: str,
    proposed_value: float,
    proposed_unit: str,
    confidence: float,
    reasoning: str,
    is_reversible: bool,
    materiality_kwh: float,
) -> str:
    """Produce a structured reconciliation recommendation.

    Args:
        exception_id: The exception being reconciled.
        evidence_summary: Summary of all evidence gathered.
        sources_agreeing: Comma-separated list of sources that agree on a value.
        sources_disagreeing: Comma-separated list of sources that disagree.
        proposed_value: The recommended correct value.
        proposed_unit: Unit of the proposed value.
        confidence: Confidence score between 0.0 and 1.0.
        reasoning: Step-by-step reasoning for the recommendation.
        is_reversible: Whether this correction can be undone.
        materiality_kwh: Absolute difference in kWh from submitted value.
    """
    result = {
        "exception_id": exception_id,
        "recommendation": {
            "proposed_value": proposed_value,
            "proposed_unit": proposed_unit,
            "confidence": round(confidence, 3),
            "reasoning": reasoning,
        },
        "evidence": {
            "summary": evidence_summary,
            "sources_agreeing": [s.strip() for s in sources_agreeing.split(",") if s.strip()],
            "sources_disagreeing": [s.strip() for s in sources_disagreeing.split(",") if s.strip()],
        },
        "risk_assessment": {
            "is_reversible": is_reversible,
            "materiality_kwh": materiality_kwh,
        },
    }
    return json.dumps(result, indent=2)


SYSTEM_PROMPT = """You are a ReconciliationAgent that synthesizes evidence from multiple
sources into a structured reconciliation recommendation.

Given evidence gathered by other agents, you must:
1. Determine which sources agree and which disagree
2. Propose the most likely correct value
3. Assign a confidence score (0.0–1.0):
   - 0.95+ when 3+ independent sources agree perfectly
   - 0.85–0.95 when 2 trusted sources agree with consistent history
   - 0.60–0.85 when sources partially agree but with some ambiguity
   - Below 0.60 when sources materially conflict
4. Assess reversibility and materiality
5. Provide clear step-by-step reasoning

NEVER inflate confidence. If sources conflict, say so and lower the score.
The policy engine downstream will decide whether to auto-resolve or escalate
based on your confidence score — your job is to be accurate, not optimistic."""


def create_reconciliation_agent(callback_handler=None) -> Agent:
    kwargs = {
        "model": f"bedrock/{BEDROCK_MODEL_ID}",
        "system_prompt": SYSTEM_PROMPT,
        "tools": [produce_reconciliation],
    }
    if callback_handler:
        kwargs["callback_handler"] = callback_handler
    return Agent(**kwargs)

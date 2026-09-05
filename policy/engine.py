"""Policy engine — deterministic function, not an agent.
Confidence + reversibility + materiality → auto-resolve or escalate."""

from config import CONFIDENCE_AUTO_RESOLVE_THRESHOLD, MATERIALITY_THRESHOLD_KWH, MATERIALITY_THRESHOLD_PCT


def apply_policy(exception_id: str, reconciliation: dict) -> dict:
    rec = reconciliation.get("recommendation", {})
    risk = reconciliation.get("risk_assessment", {})
    evidence = reconciliation.get("evidence", {})

    confidence = rec.get("confidence", 0)
    is_reversible = risk.get("is_reversible", False)
    materiality_kwh = risk.get("materiality_kwh", float("inf"))
    sources_agreeing = evidence.get("sources_agreeing", [])
    sources_disagreeing = evidence.get("sources_disagreeing", [])

    reasons = []

    if confidence >= CONFIDENCE_AUTO_RESOLVE_THRESHOLD:
        reasons.append(f"confidence {confidence:.3f} >= threshold {CONFIDENCE_AUTO_RESOLVE_THRESHOLD}")
    else:
        reasons.append(f"confidence {confidence:.3f} < threshold {CONFIDENCE_AUTO_RESOLVE_THRESHOLD}")

    if is_reversible:
        reasons.append("correction is reversible")
    else:
        reasons.append("correction is NOT reversible")

    is_material = materiality_kwh > MATERIALITY_THRESHOLD_KWH
    if is_material:
        reasons.append(f"materiality {materiality_kwh} kWh > threshold {MATERIALITY_THRESHOLD_KWH} kWh")
    else:
        reasons.append(f"materiality {materiality_kwh} kWh <= threshold {MATERIALITY_THRESHOLD_KWH} kWh")

    can_auto_resolve = (
        confidence >= CONFIDENCE_AUTO_RESOLVE_THRESHOLD
        and is_reversible
        and len(sources_agreeing) >= 2
    )

    if len(sources_disagreeing) >= 2 and confidence < 0.60:
        action = "escalate"
        policy = "conflicting_sources_low_confidence"
        reasons.append(f"{len(sources_disagreeing)} sources disagree with confidence < 0.60 → escalate")
    elif can_auto_resolve:
        action = "auto_resolve"
        policy = "high_confidence_reversible_multi_source"
        reasons.append(f"{len(sources_agreeing)} sources agree, reversible, high confidence → auto-resolve")
    elif confidence >= 0.60:
        action = "escalate"
        policy = "moderate_confidence_needs_review"
        reasons.append("moderate confidence — needs human review")
    else:
        action = "escalate"
        policy = "low_confidence"
        reasons.append("low confidence — requires human investigation")

    return {
        "exception_id": exception_id,
        "action": action,
        "policy": policy,
        "confidence": confidence,
        "proposed_value": rec.get("proposed_value"),
        "reasoning": "; ".join(reasons),
        "sources_agreeing": sources_agreeing,
        "sources_disagreeing": sources_disagreeing,
    }

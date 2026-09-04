"""Tests for deterministic detectors."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import reset_db
from db.seed import seed_all
from detectors import detect_historical_deviation, detect_missing_data, detect_cross_source_mismatch


def setup_module():
    seed_all()


def test_historical_deviation_scenario_a():
    results = detect_historical_deviation("SUP-001", "FAC-GT-01", "electricity", "2026-07")
    assert len(results) == 1
    assert results[0]["exception_type"] == "historical_deviation"
    assert results[0]["deviation_pct"] > 300


def test_missing_data_scenario_b():
    results = detect_missing_data("2026-09")
    supplier_ids = [r["supplier_id"] for r in results]
    assert "SUP-002" in supplier_ids


def test_cross_source_mismatch_scenario_c():
    results = detect_cross_source_mismatch("SUP-003", "FAC-PC-01", "electricity", "2026-08")
    assert len(results) == 1
    assert results[0]["exception_type"] == "cross_source_mismatch"
    assert results[0]["num_conflicting_groups"] >= 2


def test_no_deviation_within_threshold():
    results = detect_historical_deviation("SUP-002", "FAC-AC-01", "electricity", "2026-08")
    assert len(results) == 0


def test_policy_auto_resolve():
    from policy.engine import apply_policy
    reconciliation = {
        "recommendation": {"proposed_value": 18420, "proposed_unit": "kWh", "confidence": 0.95, "reasoning": "test"},
        "evidence": {"sources_agreeing": ["invoice", "erp"], "sources_disagreeing": ["supplier_submission"]},
        "risk_assessment": {"is_reversible": True, "materiality_kwh": 65780},
    }
    decision = apply_policy("EXC-TEST", reconciliation)
    assert decision["action"] == "auto_resolve"


def test_policy_escalate_low_confidence():
    from policy.engine import apply_policy
    reconciliation = {
        "recommendation": {"proposed_value": 18420, "proposed_unit": "kWh", "confidence": 0.45, "reasoning": "test"},
        "evidence": {"sources_agreeing": ["invoice"], "sources_disagreeing": ["erp", "meter"]},
        "risk_assessment": {"is_reversible": True, "materiality_kwh": 65780},
    }
    decision = apply_policy("EXC-TEST", reconciliation)
    assert decision["action"] == "escalate"

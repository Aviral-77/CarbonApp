"""Run all deterministic detectors against the seed data."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from db.seed import seed_all
from detectors import detect_historical_deviation, detect_missing_data, detect_cross_source_mismatch


def main():
    print("=== Resetting and seeding database ===")
    seed_all()
    print()

    print("=== Detector: Historical Deviation ===")
    # Scenario A: GreenTech Jul 2026 — should flag 84,200 vs ~18,700 avg
    results = detect_historical_deviation("SUP-001", "FAC-GT-01", "electricity", "2026-07")
    for r in results:
        print(f"  FLAGGED: {r['exception_type']} — submitted {r['submitted_value']}, "
              f"mean {r['historical_mean']}, deviation {r['deviation_pct']}%")
    if not results:
        print("  No anomalies detected")
    print()

    print("=== Detector: Missing Data ===")
    # Scenario B: Acme Mfg missing Sep 2026
    results = detect_missing_data("2026-09")
    for r in results:
        print(f"  FLAGGED: {r['exception_type']} — {r['supplier_name']} missing {r['expected_period']}, "
              f"last submission: {r['last_submission_period']}")
    if not results:
        print("  No missing data detected")
    print()

    print("=== Detector: Cross-Source Mismatch ===")
    # Scenario C: Pacific Coast Logistics Aug 2026 — 4 conflicting sources
    results = detect_cross_source_mismatch("SUP-003", "FAC-PC-01", "electricity", "2026-08")
    for r in results:
        print(f"  FLAGGED: {r['exception_type']} — {r['num_conflicting_groups']} groups, "
              f"spread {r['spread_pct']}%")
        for src, val in r['sources'].items():
            print(f"    {src}: {val}")
    if not results:
        print("  No mismatches detected")
    print()

    print("=== All detectors complete ===")


if __name__ == "__main__":
    main()

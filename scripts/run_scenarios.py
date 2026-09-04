"""Run all three demo scenarios end-to-end via the orchestrator."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from db.seed import seed_all
from agents.orchestrator import investigate_exception


def main():
    print("=== Resetting and seeding database ===")
    seed_all()
    print()

    scenarios = [
        ("EXC-A001", "Scenario A — Auto-resolve (transcription error)"),
        ("EXC-B001", "Scenario B — Supplier clarification (missing data)"),
        ("EXC-C001", "Scenario C — Human escalation (conflicting evidence)"),
    ]

    for exc_id, description in scenarios:
        print(f"\n{'='*60}")
        print(f"  {description}")
        print(f"  Exception: {exc_id}")
        print(f"{'='*60}\n")

        try:
            result = investigate_exception(exc_id)
            print(f"\n--- Result ---\n{result}\n")
        except Exception as e:
            print(f"\n--- Error ---\n{e}\n")

    print("\n=== All scenarios complete ===")


if __name__ == "__main__":
    main()

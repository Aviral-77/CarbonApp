"""Seed data for the three demo scenarios."""
import uuid
from db import get_connection, init_db


def seed_suppliers(conn):
    suppliers = [
        ("SUP-001", "GreenTech Manufacturing", "ops@greentech-mfg.com"),
        ("SUP-002", "Acme Mfg", "sustainability@acme-mfg.com"),
        ("SUP-003", "Pacific Coast Logistics", "carbon@pclogistics.com"),
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO suppliers (id, name, contact_email) VALUES (?, ?, ?)",
        suppliers,
    )


def seed_scenario_a(conn):
    """Scenario A — Auto-resolve (transcription error).
    Submitted: 84,200 kWh  Invoice: 18,420 kWh  ERP: 18,420 kWh  History: ~18,700 kWh
    Digit transposition: 18,420 → 84,200. Two trusted sources agree, reversible, low materiality.
    """
    record_id = "REC-A001"
    conn.execute(
        """INSERT OR REPLACE INTO activity_records
        (id, supplier_id, facility_id, activity_type, reporting_period, quantity, unit, source, raw_reference)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (record_id, "SUP-001", "FAC-GT-01", "electricity", "2026-07",
         84200.0, "kWh", "supplier_submission", None),
    )
    # Invoice record
    conn.execute(
        """INSERT OR REPLACE INTO activity_records
        (id, supplier_id, facility_id, activity_type, reporting_period, quantity, unit, source, raw_reference)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("REC-A001-INV", "SUP-001", "FAC-GT-01", "electricity", "2026-07",
         18420.0, "kWh", "invoice", "data/invoices/greentech_jul2026.pdf"),
    )
    # ERP record
    conn.execute(
        """INSERT OR REPLACE INTO activity_records
        (id, supplier_id, facility_id, activity_type, reporting_period, quantity, unit, source, raw_reference)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("REC-A001-ERP", "SUP-001", "FAC-GT-01", "electricity", "2026-07",
         18420.0, "kWh", "erp", "data/erp/greentech_jul2026.json"),
    )
    # Historical records (past 6 months for baseline)
    history = [
        ("REC-A-H1", "2026-01", 18350.0),
        ("REC-A-H2", "2026-02", 18520.0),
        ("REC-A-H3", "2026-03", 18680.0),
        ("REC-A-H4", "2026-04", 18900.0),
        ("REC-A-H5", "2026-05", 18750.0),
        ("REC-A-H6", "2026-06", 18600.0),
    ]
    for rec_id, period, qty in history:
        conn.execute(
            """INSERT OR REPLACE INTO activity_records
            (id, supplier_id, facility_id, activity_type, reporting_period, quantity, unit, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (rec_id, "SUP-001", "FAC-GT-01", "electricity", period, qty, "kWh", "supplier_submission"),
        )
    # Pre-seed the exception
    conn.execute(
        """INSERT OR REPLACE INTO exceptions
        (id, record_id, supplier_id, exception_type, status, severity, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("EXC-A001", record_id, "SUP-001", "transcription_error", "open", "medium",
         "Submitted value 84,200 kWh deviates 350% from historical average ~18,700 kWh"),
    )


def seed_scenario_b(conn):
    """Scenario B — Supplier clarification (missing data).
    Expected September submission from Acme Mfg — not received.
    """
    # Historical records only — no current submission
    history = [
        ("REC-B-H1", "2026-01", 42100.0),
        ("REC-B-H2", "2026-02", 41800.0),
        ("REC-B-H3", "2026-03", 43200.0),
        ("REC-B-H4", "2026-04", 42500.0),
        ("REC-B-H5", "2026-05", 41900.0),
        ("REC-B-H6", "2026-06", 42800.0),
        ("REC-B-H7", "2026-07", 43100.0),
        ("REC-B-H8", "2026-08", 42700.0),
    ]
    for rec_id, period, qty in history:
        conn.execute(
            """INSERT OR REPLACE INTO activity_records
            (id, supplier_id, facility_id, activity_type, reporting_period, quantity, unit, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (rec_id, "SUP-002", "FAC-AC-01", "electricity", period, qty, "kWh", "supplier_submission"),
        )
    conn.execute(
        """INSERT OR REPLACE INTO exceptions
        (id, record_id, supplier_id, exception_type, status, severity, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("EXC-B001", None, "SUP-002", "missing_data", "open", "medium",
         "Expected September 2026 electricity submission from Acme Mfg not received. Last submission: August 2026."),
    )


def seed_scenario_c(conn):
    """Scenario C — Human escalation (conflicting evidence).
    CSV: 84,200  Invoice: 18,420  ERP: 84,200  Meter: 21,000
    Sources disagree — agent refuses to resolve, escalates with full evidence bundle.
    """
    records = [
        ("REC-C001", 84200.0, "supplier_submission", None),
        ("REC-C001-INV", 18420.0, "invoice", "data/invoices/pclogistics_aug2026.pdf"),
        ("REC-C001-ERP", 84200.0, "erp", "data/erp/pclogistics_aug2026.json"),
        ("REC-C001-MTR", 21000.0, "meter", "data/meters/pclogistics_aug2026.json"),
    ]
    for rec_id, qty, source, ref in records:
        conn.execute(
            """INSERT OR REPLACE INTO activity_records
            (id, supplier_id, facility_id, activity_type, reporting_period, quantity, unit, source, raw_reference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (rec_id, "SUP-003", "FAC-PC-01", "electricity", "2026-08",
             qty, "kWh", source, ref),
        )
    # Historical
    history = [
        ("REC-C-H1", "2026-02", 20500.0),
        ("REC-C-H2", "2026-03", 20800.0),
        ("REC-C-H3", "2026-04", 21200.0),
        ("REC-C-H4", "2026-05", 20900.0),
        ("REC-C-H5", "2026-06", 21100.0),
        ("REC-C-H6", "2026-07", 20700.0),
    ]
    for rec_id, period, qty in history:
        conn.execute(
            """INSERT OR REPLACE INTO activity_records
            (id, supplier_id, facility_id, activity_type, reporting_period, quantity, unit, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (rec_id, "SUP-003", "FAC-PC-01", "electricity", period, qty, "kWh", "supplier_submission"),
        )
    conn.execute(
        """INSERT OR REPLACE INTO exceptions
        (id, record_id, supplier_id, exception_type, status, severity, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("EXC-C001", "REC-C001", "SUP-003", "cross_source_mismatch", "open", "high",
         "Four sources report conflicting values: CSV 84,200 / Invoice 18,420 / ERP 84,200 / Meter 21,000 kWh"),
    )


def seed_all():
    init_db()
    conn = get_connection()
    seed_suppliers(conn)
    seed_scenario_a(conn)
    seed_scenario_b(conn)
    seed_scenario_c(conn)
    conn.commit()
    conn.close()
    print("Database seeded with 3 demo scenarios.")


if __name__ == "__main__":
    seed_all()

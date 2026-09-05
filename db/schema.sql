CREATE TABLE IF NOT EXISTS suppliers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    contact_email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_records (
    id TEXT PRIMARY KEY,
    supplier_id TEXT NOT NULL REFERENCES suppliers(id),
    facility_id TEXT NOT NULL,
    activity_type TEXT NOT NULL,  -- electricity, natural_gas, diesel, water
    reporting_period TEXT NOT NULL,  -- YYYY-MM
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,  -- kWh, therms, gallons, m3
    source TEXT NOT NULL DEFAULT 'supplier_submission',  -- supplier_submission, invoice, erp, meter
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_reference TEXT  -- path to source document
);

CREATE TABLE IF NOT EXISTS exceptions (
    id TEXT PRIMARY KEY,
    record_id TEXT REFERENCES activity_records(id),
    supplier_id TEXT REFERENCES suppliers(id),
    exception_type TEXT NOT NULL,  -- transcription_error, missing_data, cross_source_mismatch, historical_deviation
    status TEXT NOT NULL DEFAULT 'open',  -- open, investigating, auto_resolved, escalated, waiting
    severity TEXT DEFAULT 'medium',  -- low, medium, high, critical
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by TEXT  -- system, agent, human
);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    exception_id TEXT NOT NULL REFERENCES exceptions(id),
    source TEXT NOT NULL,  -- invoice, erp, historical, meter, supplier_submission
    field_name TEXT NOT NULL,
    value TEXT NOT NULL,
    unit TEXT,
    raw_reference TEXT,  -- path to PDF/JSON source
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exception_id TEXT NOT NULL REFERENCES exceptions(id),
    action TEXT NOT NULL,  -- detected, investigated, evidence_gathered, auto_resolved, escalated, clarification_sent
    agent TEXT,  -- orchestrator, history_agent, document_agent, erp_agent, reconciliation_agent, communicator_agent, policy_engine
    original_value TEXT,
    proposed_value TEXT,
    confidence REAL,
    reasoning TEXT,
    policy_applied TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_records_supplier ON activity_records(supplier_id);
CREATE INDEX IF NOT EXISTS idx_records_period ON activity_records(reporting_period);
CREATE INDEX IF NOT EXISTS idx_exceptions_status ON exceptions(status);
CREATE INDEX IF NOT EXISTS idx_evidence_exception ON evidence(exception_id);
CREATE INDEX IF NOT EXISTS idx_audit_exception ON audit_events(exception_id);

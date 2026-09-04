# CarbonOps

Autonomous carbon-data exception handler powered by multi-agent orchestration on AWS Bedrock.

Watches supplier and operational carbon data, investigates anomalies across sources (invoices, ERP, meter readings, historical baselines), auto-resolves what it safely can, and escalates the rest with full evidence. Never guesses.

## Architecture

**Pattern: agents-as-tools.** Small specialist agents, each with one job and 1-2 tools, composed under an orchestrator. Deterministic logic stays deterministic.

```
                    ORCHESTRATOR (Strands agent)
                    decides which specialists to call, in what order
                              |
        +----------+----------+----------+-------------+
        |          |          |          |             |
   HistoryAgent DocumentAgent ERPAgent  ReconciliationAgent  CommunicatorAgent
   (baseline    (reads       (queries   (structured output:  (drafts supplier
   reasoning)   invoice PDF) ERP record) value/confidence/    clarification —
                                          reasoning)           simulated, not sent)
        |          |          |          |             |
        +----------+----------+----------+-------------+
                              |
                       POLICY ENGINE (plain Python function, not an agent)
                       confidence + reversibility + materiality → resolve or escalate
                              |
                       AUDIT TRAIL (append-only log)
                              |
                       UI (streams the trace live)
```

## Demo Scenarios

| Scenario | Input | Outcome |
|---|---|---|
| A — Auto-resolve | Submitted: 84,200 kWh / Invoice: 18,420 / ERP: 18,420 / History: ~18,700 | Auto-corrected (digit transposition) |
| B — Clarification | Expected Sep submission from Acme Mfg not received | Clarification email drafted and logged |
| C — Escalation | CSV: 84,200 / Invoice: 18,420 / ERP: 84,200 / Meter: 21,000 | Escalated with full evidence bundle |

## Quick Start

```bash
# Install Python dependencies
pip install -e .

# Seed the database
python db/seed.py

# Run detectors against seed data
python scripts/run_detectors.py

# Test Bedrock credentials
python scripts/hello_bedrock.py

# Start the API server
uvicorn api.app:app --reload

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

## Tech Stack

- **Agents:** [Strands Agents SDK](https://github.com/strands-agents/sdk-python) on Amazon Bedrock
- **Backend:** FastAPI + SQLite
- **Frontend:** React + Vite
- **Infrastructure:** Amazon Bedrock, (optional) Amazon Bedrock AgentCore

## AWS Setup

See the AWS Setup section in the project documentation for:
1. AWS account and IAM configuration
2. Amazon Bedrock model access
3. Environment variables (AWS_REGION, AWS_ACCESS_KEY_ID, etc.)

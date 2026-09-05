import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "db" / "carbonops.db"
DATA_DIR = BASE_DIR / "data"
INVOICES_DIR = DATA_DIR / "invoices"

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514")

CONFIDENCE_AUTO_RESOLVE_THRESHOLD = 0.85
MATERIALITY_THRESHOLD_KWH = 500
MATERIALITY_THRESHOLD_PCT = 0.05

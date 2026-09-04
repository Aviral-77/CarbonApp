"""DocumentAgent — extracts data from invoice PDFs and documents."""
import json
from pathlib import Path

from strands import Agent, tool

from config import BEDROCK_MODEL_ID, BASE_DIR


@tool
def read_invoice_pdf(file_path: str) -> str:
    """Read and extract structured data from an invoice PDF.

    Args:
        file_path: Path to the PDF file relative to the project root.
    """
    full_path = BASE_DIR / file_path
    if not full_path.exists():
        # Fall back to a simulated extraction for demo
        return _simulate_pdf_extraction(file_path)

    try:
        from pypdf import PdfReader
        reader = PdfReader(str(full_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return json.dumps({
            "source": file_path,
            "extracted_text": text[:3000],
            "num_pages": len(reader.pages),
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to read PDF: {e}", "source": file_path})


def _simulate_pdf_extraction(file_path: str) -> str:
    """Simulated PDF data for demo scenarios when actual PDFs aren't available."""
    simulated = {
        "data/invoices/greentech_jul2026.pdf": {
            "vendor": "GreenTech Manufacturing",
            "invoice_number": "INV-2026-07-4521",
            "period": "July 2026",
            "line_items": [
                {"description": "Electricity - Main Facility", "quantity": 18420.0, "unit": "kWh", "rate": 0.12, "total": 2210.40}
            ],
            "total_amount": 2210.40,
            "currency": "USD",
        },
        "data/invoices/pclogistics_aug2026.pdf": {
            "vendor": "Pacific Coast Logistics",
            "invoice_number": "INV-2026-08-8834",
            "period": "August 2026",
            "line_items": [
                {"description": "Electricity - Warehouse", "quantity": 18420.0, "unit": "kWh", "rate": 0.11, "total": 2026.20}
            ],
            "total_amount": 2026.20,
            "currency": "USD",
        },
    }
    data = simulated.get(file_path)
    if data:
        return json.dumps({"source": file_path, "extracted_data": data, "method": "simulated"})
    return json.dumps({"error": f"No PDF found at {file_path}", "source": file_path})


@tool
def read_json_document(file_path: str) -> str:
    """Read a JSON data file (ERP export, meter reading, etc.).

    Args:
        file_path: Path to the JSON file relative to the project root.
    """
    full_path = BASE_DIR / file_path
    if not full_path.exists():
        return json.dumps({"error": f"File not found: {file_path}"})
    try:
        data = json.loads(full_path.read_text())
        return json.dumps({"source": file_path, "data": data})
    except Exception as e:
        return json.dumps({"error": f"Failed to read JSON: {e}", "source": file_path})


SYSTEM_PROMPT = """You are a DocumentAgent specializing in extracting carbon emissions data
from documents — invoices, PDFs, and structured data files.

When asked to investigate a record:
1. Read the referenced documents (invoices, ERP exports, meter readings)
2. Extract the relevant quantity, unit, and any context
3. Report exactly what each document says — never infer or estimate

Always cite the specific document and field where you found each value.
If a document is unavailable, say so explicitly rather than guessing."""


def create_document_agent(callback_handler=None) -> Agent:
    kwargs = {
        "model": f"bedrock/{BEDROCK_MODEL_ID}",
        "system_prompt": SYSTEM_PROMPT,
        "tools": [read_invoice_pdf, read_json_document],
    }
    if callback_handler:
        kwargs["callback_handler"] = callback_handler
    return Agent(**kwargs)

"""Extracts candidate epiphanic passages from a PDF using the Claude API."""

from datetime import date
import hashlib
import json
import os
from pathlib import Path

import fitz
from anthropic import Anthropic


CHUNK_SIZE = 15000
MODEL_NAME = "claude-sonnet-4-6"
SYSTEM_PROMPT = "You are a precise research assistant. Follow instructions exactly."
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "pdf_extraction_prompt.txt"


class PDFExtractionError(Exception):
    pass


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def _extract_pdf_text(file_path: str) -> str:
    try:
        document = fitz.open(file_path)
    except Exception as error:
        raise PDFExtractionError(f"Unable to open PDF: {str(error)}") from None

    try:
        pages = [page.get_text() for page in document]
    finally:
        document.close()

    extracted_text = "\n".join(pages).strip()
    if len(extracted_text) < 100:
        raise PDFExtractionError(
            "This PDF appears to contain no extractable text. Scanned or image-only PDFs are not supported in this version."
        )

    return extracted_text


def _chunk_text(text: str) -> list[str]:
    return [text[index : index + CHUNK_SIZE] for index in range(0, len(text), CHUNK_SIZE)]


def _extract_response_text(response) -> str:
    parts = []
    for block in getattr(response, "content", []):
        block_text = getattr(block, "text", "")
        if block_text:
            parts.append(block_text)
    return "".join(parts).strip()


def _strip_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _call_claude(client: Anthropic, prompt: str, chunk_text: str) -> list[dict]:
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\n{chunk_text}",
                }
            ],
        )
    except Exception as error:
        raise PDFExtractionError(f"Anthropic API call failed: {str(error)}") from None

    response_text = _strip_markdown_fences(_extract_response_text(response))
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise PDFExtractionError(f"Claude returned unparseable JSON: {str(error)}") from None

    if not isinstance(parsed, list):
        raise PDFExtractionError("Claude returned unparseable JSON: response was not a JSON array.")

    return parsed


def _build_record(file_path: str, passage: str, location_hint: str) -> dict:
    filename = Path(file_path).name
    normalized_passage = passage.strip()
    return {
        "record_id": f"pdf_{hashlib.md5(normalized_passage[:100].encode('utf-8')).hexdigest()}",
        "source_type": "pdf",
        "source_id": filename,
        "title": filename,
        "text": normalized_passage,
        "date_retrieved": date.today().isoformat(),
        "url": "",
        "page_ref": location_hint.strip(),
        "search_terms_used": "",
        "stage_1": "",
        "stage_2": "",
        "stage_3": "",
        "overall_verdict": "",
        "notes": "",
    }


def process_pdf(file_path: str) -> list:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise PDFExtractionError("Anthropic API key not configured. Add ANTHROPIC_API_KEY to your .env file.")

    prompt = _load_prompt()
    extracted_text = _extract_pdf_text(file_path)
    chunks = _chunk_text(extracted_text)
    client = Anthropic(api_key=api_key)

    records = []
    seen_record_ids = set()

    for chunk_text in chunks:
        passages = _call_claude(client, prompt, chunk_text)
        for item in passages:
            if not isinstance(item, dict):
                continue

            passage_text = str(item.get("passage", "")).strip()
            if not passage_text:
                continue

            location_hint = str(item.get("location_hint", "") or "")
            record = _build_record(file_path, passage_text, location_hint)
            if record["record_id"] in seen_record_ids:
                continue

            seen_record_ids.add(record["record_id"])
            records.append(record)

    return records

"""Exports collected records to CSV and JSON formats in the output directory."""

import csv
import json
from pathlib import Path


OUTPUT_DIR = Path("output")
CSV_PATH = OUTPUT_DIR / "example_bank.csv"
JSON_PATH = OUTPUT_DIR / "example_bank.json"
RECORD_FIELDS = [
    "record_id",
    "source_type",
    "source_id",
    "title",
    "text",
    "date_retrieved",
    "url",
    "page_ref",
    "search_terms_used",
    "stage_1",
    "stage_2",
    "stage_3",
    "overall_verdict",
    "notes",
]


def _load_existing_json_records() -> list:
    if not JSON_PATH.exists():
        return []

    try:
        with JSON_PATH.open("r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except json.JSONDecodeError:
        return []

    return data if isinstance(data, list) else []


def _normalize_record(record: dict) -> dict:
    return {field: record.get(field, "") for field in RECORD_FIELDS}


def export_records(records: list) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    normalized_records = [_normalize_record(record) for record in records]

    csv_exists = CSV_PATH.exists()
    with CSV_PATH.open("a", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=RECORD_FIELDS)
        if not csv_exists:
            writer.writeheader()
        writer.writerows(normalized_records)

    json_records = _load_existing_json_records()
    json_records.extend(normalized_records)
    with JSON_PATH.open("w", encoding="utf-8") as json_file:
        json.dump(json_records, json_file, indent=2)

    return len(normalized_records)

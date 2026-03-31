"""Filters already-seen records and tracks processed IDs to prevent duplicates."""

import json
from pathlib import Path


SEEN_IDS_PATH = Path("output/seen_ids.json")


def load_seen_ids() -> set[str]:
    if not SEEN_IDS_PATH.exists():
        return set()

    try:
        with SEEN_IDS_PATH.open("r", encoding="utf-8") as seen_file:
            data = json.load(seen_file)
    except json.JSONDecodeError:
        return set()

    if not isinstance(data, list):
        return set()

    return {
        str(record_id)
        for record_id in data
        if isinstance(record_id, str) and record_id.strip()
    }


def _write_seen_ids(seen_ids: set[str]) -> None:
    SEEN_IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SEEN_IDS_PATH.open("w", encoding="utf-8") as seen_file:
        json.dump(sorted(seen_ids), seen_file, indent=2)


def filter_new(records: list) -> list:
    seen_ids = load_seen_ids()
    return [
        record for record in records
        if isinstance(record, dict) and record.get("record_id") not in seen_ids
    ]


def mark_seen(records: list) -> None:
    seen_ids = load_seen_ids()
    seen_ids.update(
        record["record_id"]
        for record in records
        if isinstance(record, dict) and record.get("record_id")
    )
    _write_seen_ids(seen_ids)

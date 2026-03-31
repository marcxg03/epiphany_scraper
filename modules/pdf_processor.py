"""Extracts candidate epiphanic passages from a PDF using the Claude API."""

from datetime import date
import hashlib
import json
import logging
import os
from pathlib import Path
import re

import fitz
from anthropic import Anthropic


CHUNK_SIZE = 15000
CHUNK_OVERLAP = 3000
NEAR_DUPLICATE_PREFIX_LEN = 200
EXTRACTION_MODEL = "claude-sonnet-4-6"
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

    with document:
        page_texts = [page.get_text() for page in document]

    extracted_text = "\n".join(page_texts).strip()
    if len(extracted_text) < 100:
        raise PDFExtractionError(
            "This PDF appears to contain no extractable text. "
            "Scanned or image-only PDFs are not supported in this version."
        )

    return extracted_text


def _chunk_text(text: str) -> list[str]:
    if len(text) <= CHUNK_SIZE:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        if end >= len(text):
            chunks.append(text[start:])
            break
        # Prefer to break at a paragraph boundary to avoid splitting passages mid-sentence
        for sep in ("\n\n", "\n"):
            boundary = text.rfind(sep, start, end)
            if boundary > start:
                end = boundary
                break
        chunks.append(text[start:end])
        # Step back by CHUNK_OVERLAP so narratives crossing the boundary appear
        # in full in the next chunk; duplicates are filtered by record_id downstream
        start = end - CHUNK_OVERLAP

    return chunks


def _extract_response_text(response) -> str:
    return "".join(
        getattr(block, "text", "")
        for block in getattr(response, "content", [])
    ).strip()


def _strip_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    cleaned = cleaned.removeprefix("```json").removeprefix("```")
    return cleaned.removesuffix("```").strip()


# Greedy match from the first '[' to the last ']' — handles preamble and postamble.
_JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)


def _extract_json_array(text: str) -> str:
    """Extracts the outermost [...] array from text, stripping any preamble or postamble."""
    match = _JSON_ARRAY_RE.search(text)
    return match.group(0) if match else text


def _sanitize_json_control_chars(text: str) -> str:
    """
    Escapes literal control characters that appear inside JSON string values.

    The most common cause of 'Expecting delimiter' errors is Claude embedding a
    raw newline (0x0A) inside a passage string instead of the escape sequence \\n.
    This function finds every quoted string in the text and replaces bare control
    characters with their JSON-legal escape sequences, leaving structural whitespace
    between tokens untouched.
    """
    def _escape_string(match: re.Match) -> str:
        s = match.group(0)
        s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        # Strip remaining non-printable control characters (null bytes, etc.)
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)

    # Match JSON string literals, including those that span multiple lines.
    return re.sub(r'"(?:[^"\\]|\\.)*"', _escape_string, text, flags=re.DOTALL)


def _repair_unescaped_quotes(text: str) -> str:
    """
    Repairs JSON where string values contain unescaped double-quote characters.

    The regex-based sanitizer cannot fix this because its pattern `[^"\\]` halts
    at the first unescaped inner quote, so the string boundary is never correctly
    identified. This function walks the text character by character instead.

    Inside each JSON string, when a bare `"` is encountered, it peeks at the next
    non-whitespace character:
    - If that character is `:`, `,`, `}`, or `]` the quote closes the string.
    - Otherwise the quote is an unescaped inner character and is escaped as `\\"`.

    Control characters (raw newlines, tabs, etc.) are also escaped in the same pass,
    so this replaces both sanitization passes when unescaped quotes are present.
    """
    result: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        if ch != '"':
            result.append(ch)
            i += 1
            continue

        # Opening delimiter of a JSON string — copy it and enter string mode
        result.append('"')
        i += 1

        while i < n:
            ch = text[i]

            if ch == '\\' and i + 1 < n:
                # Already-escaped sequence — copy both chars verbatim
                result.append(ch)
                result.append(text[i + 1])
                i += 2

            elif ch == '"':
                # Peek past whitespace to decide whether this closes the string
                j = i + 1
                while j < n and text[j] in ' \t\n\r':
                    j += 1
                if j >= n or text[j] in ':,}]':
                    # This is the real closing delimiter
                    result.append('"')
                    i += 1
                    break
                else:
                    # Unescaped inner quote — escape it
                    result.append('\\"')
                    i += 1

            elif ch == '\n':
                result.append('\\n')
                i += 1
            elif ch == '\r':
                result.append('\\r')
                i += 1
            elif ch == '\t':
                result.append('\\t')
                i += 1
            elif ord(ch) < 0x20:
                i += 1  # Strip other bare control characters
            else:
                result.append(ch)
                i += 1

    return ''.join(result)


def _parse_claude_json(response_text: str) -> list:
    """
    Parses a JSON array from a Claude response with three fallback strategies:

    1. Extract the outermost [...] array and parse directly.
    2. Sanitize control characters inside string values (regex-based) and retry.
    3. Repair unescaped inner quotes via character-level state machine and retry.

    Raises PDFExtractionError with a user-facing retry message if all three fail.
    """
    candidate = _extract_json_array(response_text)

    # Attempt 1: direct parse of extracted array
    try:
        result = json.loads(candidate)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Attempt 2: sanitize control characters inside string literals, then retry
    sanitized = _sanitize_json_control_chars(candidate)
    try:
        result = json.loads(sanitized)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Attempt 3: character-level repair of unescaped inner quotes (and control chars)
    repaired = _repair_unescaped_quotes(candidate)
    try:
        result = json.loads(repaired)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    logging.warning(
        "Unparseable Claude JSON response (first 500 chars): %s", response_text[:500]
    )
    raise PDFExtractionError(
        "Claude returned unparseable JSON — try running the extraction again."
    )


def _dedup_near_duplicates(records: list[dict]) -> list[dict]:
    """Returns records with near-duplicates removed, keeping the longest of each opening."""
    deduped: list[dict] = []
    seen_prefixes: set[str] = set()
    for record in sorted(records, key=lambda r: len(r["text"]), reverse=True):
        prefix = record["text"][:NEAR_DUPLICATE_PREFIX_LEN]
        if prefix not in seen_prefixes:
            seen_prefixes.add(prefix)
            deduped.append(record)
    return deduped


def _call_claude(client: Anthropic, prompt: str, content: str) -> list[dict]:
    try:
        response = client.messages.create(
            model=EXTRACTION_MODEL,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"{prompt}\n\n{content}"}],
        )
    except Exception as error:
        raise PDFExtractionError(f"Anthropic API call failed: {str(error)}") from None

    response_text = _strip_markdown_fences(_extract_response_text(response))
    return _parse_claude_json(response_text)


def _build_record(file_path: str, passage: str, location_hint: str) -> dict:
    filename = Path(file_path).name
    normalized_passage = passage.strip()
    return {
        "record_id": f"pdf_{hashlib.md5(normalized_passage.encode('utf-8')).hexdigest()}",
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
        raise PDFExtractionError(
            "Anthropic API key not configured. Add ANTHROPIC_API_KEY to your .env file."
        )

    prompt = _load_prompt()
    extracted_text = _extract_pdf_text(file_path)
    chunks = _chunk_text(extracted_text)
    client = Anthropic(api_key=api_key)

    records = []
    seen_record_ids: set[str] = set()

    for chunk in chunks:
        raw_passages = _call_claude(client, prompt, chunk)
        for item in raw_passages:
            if not isinstance(item, dict):
                continue

            passage_text = str(item.get("passage", "") or "").strip()
            if not passage_text:
                continue

            location_hint = str(item.get("location_hint", "") or "")
            record = _build_record(file_path, passage_text, location_hint)
            if record["record_id"] in seen_record_ids:
                continue

            seen_record_ids.add(record["record_id"])
            records.append(record)

    # Near-duplicate deduplication: if two passages share the same opening
    # NEAR_DUPLICATE_PREFIX_LEN characters, keep only the longer one.
    # This catches overlap-region variants where MD5s differ but content is the same narrative.
    return _dedup_near_duplicates(records)

# SLICE_3_PDF_PROCESSOR.md
## Epiphany Narrative Example Bank — Retrieval Tool
*Slice 3 of 4: PDF Processor*

---

## Goal

Implement the PDF processor module and wire it to the UI so the user can drop in a PDF file, have its text extracted and sent to Claude, and receive candidate epiphanic passages back as structured records ready for export.

---

## Acceptance Criteria

1. Dropping a PDF into the file zone and clicking "Run PDF Extraction" returns candidate passages in the results table
2. Each record contains all required fields from the shared schema, with source_type = "pdf" and source_id = the PDF filename
3. The page_ref field is populated where Claude can identify a location hint; blank otherwise
4. Export CSV and JSON work correctly for PDF records using the same exporter module as Slice 2
5. Deduplication works for PDF records — re-processing the same PDF skips already-exported passages
6. A progress spinner shows while extraction is running
7. If the PDF contains no extractable text (scanned/image-only), a clear error message appears — not a crash
8. If Claude returns no candidate passages, a clear "No candidate passages found" message appears
9. If the Anthropic API key is missing or invalid, a clear error message appears
10. All errors surface as readable st.error() messages — no raw Python tracebacks
11. Long PDFs (15,000+ characters) are chunked and processed without crashing

---

## Files to Create or Modify

```
MODIFY:   app.py                         — enable PDF button, add extraction logic
MODIFY:   modules/pdf_processor.py       — full implementation
CREATE:   prompts/pdf_extraction_prompt.txt — the locked Claude extraction prompt
NO CHANGE: modules/reddit_scraper.py     — leave untouched
NO CHANGE: modules/deduplicator.py       — already implemented, use as-is
NO CHANGE: modules/exporter.py           — already implemented, use as-is
```

---

## Record Schema

Every PDF record must contain exactly these fields:

```
{
  "record_id":          "pdf_" + md5 hash of first 100 chars of passage text,
  "source_type":        "pdf",
  "source_id":          filename from file_path,
  "title":              filename from file_path,
  "text":               passage text from Claude response,
  "date_retrieved":     today's date YYYY-MM-DD,
  "url":                "",
  "page_ref":           location_hint from Claude response (blank if empty),
  "search_terms_used":  "",
  "stage_1":            "",
  "stage_2":            "",
  "stage_3":            "",
  "overall_verdict":    "",
  "notes":              ""
}
```

---

## Component Contracts

### modules/pdf_processor.py
```
Function: process_pdf(file_path: str) -> list

- Extract text using fitz.open(file_path), iterate pages, concatenate page.get_text()
- If total extracted text < 100 characters: raise PDFExtractionError — scanned PDF message
- Load prompt from prompts/pdf_extraction_prompt.txt
- For PDFs longer than 15,000 characters: chunk into 15,000-char sections, 
  one Claude API call per chunk, combine all results
- Claude API parameters:
    - model: claude-sonnet-4-20250514
    - max_tokens: 4000
    - system: "You are a precise research assistant. Follow instructions exactly."
- Parse JSON array from Claude response
- Strip any accidental markdown fences before parsing
- Build Record dict for each passage using schema above
- record_id: "pdf_" + hashlib.md5(passage[:100].encode()).hexdigest()
- Deduplicate within batch by record_id before returning
- Define PDFExtractionError as a custom exception class in this file
```

### app.py changes
```
- Enable PDF button when a file has been uploaded
- On file upload: store in st.session_state["pdf_file"]
- On PDF button click:
    - Save uploaded file bytes to tempfile.NamedTemporaryFile
    - Wrap in try/except — all errors via st.error()
    - Show st.spinner("Extracting passages from PDF...")
    - Call process_pdf(temp_path)
    - Call filter_new() on results
    - Store in st.session_state["records"]
    - Display results table, record count, duplicate count
    - If zero results: st.info("No candidate passages found in this PDF.")
    - Clean up temp file after processing
```

---

## Edge Cases to Handle

- Scanned/image-only PDF: detect via short extracted text, raise clean error
- Password-protected PDF: PyMuPDF fails to open, catch and show clear message
- Claude returns malformed JSON: "Extraction failed — Claude returned an unexpected response. Try again."
- Very long PDF: chunk into 15,000-character sections, multiple API calls, combine results
- File not actually a PDF despite extension: PyMuPDF raises on open, catch cleanly
- Anthropic API key missing: "Anthropic API key not configured. Add ANTHROPIC_API_KEY to your .env file."
- Duplicate passages within single PDF run: deduplicate by record_id before returning

---

## Test Cases

1. Drop in a journal article PDF — candidate passages appear in results table
2. Drop in the same PDF again — "X duplicates skipped" message appears
3. Drop in a scanned PDF — clean error message appears, no crash
4. Export after PDF extraction — CSV and JSON contain PDF records with correct schema
5. Mix Reddit and PDF records in one session — all export correctly together
6. Very long PDF (50+ pages) — tool handles without crashing

---

## Codex Generation Prompt

```
CONTEXT:
I am building a local research tool called the Epiphany Narrative Example Bank Retrieval Tool — a Python + Streamlit web app. The project folder is epiphany_scraper. Slices 1 and 2 are complete — the scaffold is in place and the Reddit scraper is fully working. This is Slice 3: implementing the PDF processor module and wiring it to the UI.

TASK:
Implement the PDF processor module in full and update app.py to enable the PDF panel. The user should be able to drop a PDF into the file zone, click Run PDF Extraction, and receive candidate epiphanic passages back as structured records in the results table.

FILES TO MODIFY:
1. app.py — enable PDF button, add extraction logic, wire results to existing display and export system
2. modules/pdf_processor.py — full implementation using PyMuPDF and Anthropic SDK

FILES TO CREATE:
3. prompts/pdf_extraction_prompt.txt — paste the exact prompt text provided below

DO NOT MODIFY:
- modules/reddit_scraper.py — leave completely untouched
- modules/deduplicator.py — already implemented, use as-is
- modules/exporter.py — already implemented, use as-is
- requirements.txt — all packages already installed
- .env — never touch credentials files
- anything in the docs/ folder

CONSTRAINTS:
- Python 3.11+, Streamlit only for UI
- Use PyMuPDF imported as fitz for PDF text extraction
- Use the Anthropic Python SDK for Claude API calls
- Credentials loaded from .env only via python-dotenv — never hardcoded
- All errors caught and displayed via st.error() — no raw Python tracebacks
- Use st.session_state to store records — same pattern as Slice 2
- Reuse existing deduplicator and exporter modules unchanged

RECORD SCHEMA — every PDF record must contain exactly these fields:
{
  "record_id":          "pdf_" + md5 hash of first 100 chars of passage text,
  "source_type":        "pdf",
  "source_id":          filename from file_path,
  "title":              filename from file_path,
  "text":               passage text from Claude response,
  "date_retrieved":     today's date YYYY-MM-DD,
  "url":                "",
  "page_ref":           location_hint from Claude response (blank if empty),
  "search_terms_used":  "",
  "stage_1":            "",
  "stage_2":            "",
  "stage_3":            "",
  "overall_verdict":    "",
  "notes":              ""
}

PDF PROCESSOR REQUIREMENTS (modules/pdf_processor.py):
- Function signature: process_pdf(file_path: str) -> list
- Extract text using fitz.open(file_path), iterate pages, concatenate page.get_text()
- If total extracted text length < 100 characters: raise PDFExtractionError with message "This PDF appears to contain no extractable text. Scanned or image-only PDFs are not supported in this version."
- Load prompt from prompts/pdf_extraction_prompt.txt
- For PDFs longer than 15,000 characters: chunk text into sections of 15,000 characters each, make one Claude API call per chunk, combine all results
- For each chunk: append chunk text to the loaded prompt and send to Claude
- Claude API call parameters:
    - model: "claude-sonnet-4-20250514"
    - max_tokens: 4000
    - system: "You are a precise research assistant. Follow instructions exactly."
- Parse JSON array from Claude response text
- Strip any accidental markdown fences (```json or ```) before parsing
- Build Record dict for each passage using schema above
- record_id: "pdf_" + hashlib.md5(passage["passage"][:100].encode()).hexdigest()
- Deduplicate within the current batch by record_id before returning
- Define PDFExtractionError as a custom exception class in this file
- Raise PDFExtractionError with readable messages for:
    - PyMuPDF cannot open the file
    - Claude returns unparseable JSON
    - Anthropic API call fails

APP.PY CHANGES:
- Import pdf_processor module
- On file upload: store uploaded file in st.session_state["pdf_file"]
- PDF button enabled when st.session_state.get("pdf_file") is not None
- On PDF button click:
    - Save uploaded file bytes to a temp file path using tempfile.NamedTemporaryFile
    - Wrap entire operation in try/except PDFExtractionError and except Exception
    - Show st.spinner("Extracting passages from PDF...")
    - Call pdf_processor.process_pdf(temp_path)
    - Call deduplicator.filter_new() on results
    - Store in st.session_state["records"]
    - Store duplicate count in st.session_state["duplicate_count"]
    - Display results using existing st.dataframe() pattern from Slice 2
    - Show record count and duplicate count messages
    - If zero results: st.info("No candidate passages found in this PDF.")
    - Clean up temp file after processing
- PDFExtractionError: st.error(str(e))
- Missing API key: st.error("Anthropic API key not configured. Add ANTHROPIC_API_KEY to your .env file.")
- Any other exception: st.error(f"Unexpected error: {str(e)}")
- Export buttons, results table, and export logic remain exactly as implemented in Slice 2

PROMPTS/PDF_EXTRACTION_PROMPT.TXT — write this exact content:
You are a research assistant supporting a graduate researcher studying
epiphanic sequences in life story narratives. Your task is to identify and
extract candidate passages from the text provided.

---

CONSTRUCT DEFINITION

An epiphanic sequence is a first-person narrative account in which a person
recounts a sudden meaning-making moment — a discrete point in time at which
a clear, propositional insight about the self or world arrived instantaneously
rather than through gradual reflection — and which has been coherently
integrated into their life story as an ongoing interpretive reference point.

---

THE THREE STAGES

STAGE 1 — Antecedent Discrepancy
The narrator describes a prior state in which situational meaning (the
appraisal of a specific event or experience) was in tension with global
meaning (their broader beliefs, goals, or felt sense of purpose). This tension
created pressure that could not be resolved by simply absorbing the new
experience into existing beliefs — something had to reorganize.

Important: This stage is valence-neutral. The discrepancy does not require
negative emotional content — it can manifest as turmoil, wonder, confusion,
existential questioning, or any state in which existing meaning was
insufficient. It also does not require the narrator to have been consciously
aware of the discrepancy at the time — retrospective recognition counts.

STAGE 2 — Sudden Meaning-Making Moment
A discrete moment in which meaning arrived instantaneously rather than through
deliberation or gradual reflection. The meaning descended rather than was
derived. This stage requires both of the following features to be present in
the narrator's own language:

  (a) Temporal location — the realization is placed at a specific discrete
      moment rather than distributed across a period of gradual change.
      Look for language like: "in that moment I knew," "it suddenly hit me
      that," "I realized right then."
      Contrast with: "looking back I came to realize," "over time I
      understood," "I gradually came to see" — these do not qualify.

  (b) Articulability — the narrator states a clear, propositional realization
      as the content of the moment. The insight is expressible as a specific,
      bounded claim about the self or world: "I knew I had been living a lie,"
      "I realized I had always wanted to be a nurse," "I understood for the
      first time that my life had meaning."
      Contrast with diffuse felt shifts: "something shifted," "I felt
      different" — these do not qualify without propositional content.

Critical distinction: A sudden event is not the same as a sudden realization.
A narrator who describes an abrupt external occurrence that catalyzed gradual
change is describing a turning point, not an epiphany. Extract only passages
where the realization itself — not merely the precipitating event — is
temporally located and propositionally stated.

STAGE 3 — Narrative Integration
The narrator weaves the sudden meaning-making moment into their life story in
a coherent, identity-relevant way. This requires evidence of all three of the
following:

  (a) Temporal and causal arc — the epiphany is situated within a clear
      before/after structure in the life story
  (b) Psychological elaboration — sufficient internal context is provided to
      convey the personal significance of the moment to the narrator
  (c) Explicit self-interpretation — the narrator connects the realization to
      broader self-conception, personal development, or life philosophy;
      explains how it changed how they live, understand themselves, or make
      sense of subsequent experience

Note: Narrative integration is measured at the time of narration — it reflects
current integration, not a permanent property of the event.

---

YOUR TASK

Read the following text carefully. Extract every passage that contains
evidence of one or more of these three stages. Cast a wide net — include
passages that show only partial evidence (one or two stages present) as well
as passages that appear to show all three. Include near-misses where a stage
is almost but not quite satisfied.

Do not score or judge the passages. Do not apply the coding scheme. Do not
add commentary. Simply extract candidate passages for a human researcher
to review.

Return your response as a JSON array in this exact format:
[
  {
    "passage": "the exact text of the passage as it appears in the source",
    "location_hint": "page number or section heading if identifiable,
                     otherwise leave blank"
  }
]

Return only the JSON array. No preamble. No explanation. No markdown
formatting. No code fences.
If no candidate passages are found, return an empty array: []

[EXTRACTED TEXT BELOW]

ACCEPTANCE CRITERIA:
1. Dropping a PDF and clicking Run PDF Extraction returns candidate passages in results table
2. Each record contains all fields from the schema with correct source_type and source_id
3. page_ref populated from Claude location_hint where available
4. Export CSV and JSON work correctly for PDF records using existing exporter
5. Deduplication works — re-processing same PDF skips already-exported passages
6. Progress spinner shows during extraction
7. Scanned/image-only PDFs show clean error message
8. All errors surface as readable st.error() messages
9. Long PDFs chunked and processed without crashing

DO NOT:
- Modify reddit_scraper.py, deduplicator.py, or exporter.py
- Hardcode any credentials
- Change the folder structure
- Add features outside this slice
- Show raw Python tracebacks to the user

OUTPUT:
Write the complete implementation for all files listed above. Do not explain what you are doing — just produce the code. After writing, list any assumptions you made.
```

---

## Claude Code Debugging Prompt

```
CONTEXT:
I am building a local research tool called the Epiphany Narrative Example Bank Retrieval Tool — a Python + Streamlit web app. Slice 3 (PDF processor) was just generated by Codex. Dropping a PDF into the file zone and clicking Run PDF Extraction should return candidate epiphanic passages in the results table.

CURRENT PROBLEM:
[Describe exactly what isn't working — paste any error messages here]

RELEVANT FILES:
- app.py
- modules/pdf_processor.py
- prompts/pdf_extraction_prompt.txt

WHAT CODEX BUILT:
[Brief summary — e.g. "PDF uploads but extraction returns empty results" or "API call fails"]

CONSTRAINTS:
- Python 3.11+, Streamlit only for UI
- PyMuPDF imports as fitz — not pymupdf
- Do not modify reddit_scraper.py, deduplicator.py, or exporter.py
- All errors must surface via st.error() — no raw tracebacks

ACCEPTANCE CRITERIA:
1. PDF extraction returns candidate passages in results table
2. All record fields populated correctly
3. Long PDFs chunked correctly without crashing
4. Scanned PDFs show clean error message
5. All errors shown as readable messages

DO NOT:
- Rewrite files that are working correctly
- Modify any module outside pdf_processor.py and app.py
- Add features outside this slice

OUTPUT:
Fix the problem described above. Summarize what was changed, why, and list follow-up issues for the next session.
```

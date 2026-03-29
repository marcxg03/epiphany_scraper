# MASTER_SPEC.md
## Epiphany Narrative Example Bank — Retrieval Tool
*Version 1.0*

---

## 1. Problem Statement

Manually collecting first-person narrative accounts for epiphanic sequence coding is slow, unsystematic, and difficult to scale. This tool automates the retrieval and extraction step across two source types — Reddit posts and PDF documents — producing a unified, consistently structured candidate bank ready for manual prime-test coding.

---

## 2. Target Users

**Primary user:** A single graduate researcher running the tool locally on a personal Mac.

**Technical level:** Beginner. The tool must be runnable without command-line interaction after initial setup. All inputs and controls live in the browser UI.

---

## 3. User Stories

1. As a researcher, I want to paste a subreddit URL and retrieve full-text posts matching my search terms, so that I can build a pool of Reddit-sourced candidate accounts without manual browsing.
2. As a researcher, I want to edit my search terms directly in the UI before each run, so that I can refine my retrieval strategy without touching any code.
3. As a researcher, I want to drop a PDF into the tool and receive extracted candidate passages, so that I can source epiphanic accounts from books, articles, and transcripts as well as Reddit.
4. As a researcher, I want all results exported to both CSV and JSON with consistent fields, so that I can annotate and code them in Excel or Google Sheets.
5. As a researcher, I want the tool to avoid duplicating records I've already retrieved, so that re-running the tool with new parameters doesn't pollute my dataset.
6. As a researcher, I want blank coding fields pre-populated in every export record, so that my annotation workflow is ready to use immediately after export.

---

## 4. Feature List

### P0 — Core (Must Have)
1. Reddit scraper: retrieve posts by subreddit URL + search terms
2. Reddit scraper: filter posts by minimum character length
3. Reddit scraper: store full post body, not just title
4. PDF processor: extract full text from dropped PDF
5. PDF processor: send extracted text to Claude API to identify candidate passages
6. Unified output schema across both source types
7. Export to CSV and JSON
8. Deduplication — no repeated records across runs

### P1 — Important
9. Progress indicator while retrieval or extraction is running
10. Configurable minimum post length threshold in the UI
11. Results preview table in the UI before export
12. Ability to retrieve from multiple subreddits in one session
13. Page number or location reference for PDF passages where extractable

### P2 — Nice to Have
14. Filter Reddit results by date range
15. Export a run summary (how many records retrieved, source breakdown)
16. Light duplicate flagging — surface near-matches for researcher review

---

## 5. Screens and Flows

### UI Layout — Single Page

**Reddit Panel**
- Text input field: paste subreddit URL
- Text input field: search terms (editable, comma-separated)
- Number input: minimum post length (characters)
- Button: Run Reddit Scrape
- Status indicator: idle / running / complete / error

**PDF Panel**
- File drop zone: drag and drop a PDF file
- Button: Run PDF Extraction
- Status indicator: idle / running / complete / error

**Results Area (shared, below both panels)**
- Preview table showing most recent batch of retrieved records
- Button: Export CSV
- Button: Export JSON
- Record count display: "X new records retrieved. Y total records in bank."

### User Flow — Reddit
1. User pastes subreddit URL
2. User reviews/edits search terms
3. User sets minimum post length
4. User clicks Run
5. Tool queries Reddit API, retrieves matching posts, filters by length, deduplicates
6. Results appear in preview table
7. User clicks Export

### User Flow — PDF
1. User drops PDF into file zone
2. User clicks Run
3. Tool extracts text, sends to Claude API, receives candidate passages
4. Results appear in preview table
5. User clicks Export

---

## 6. Data Model

Every record in the example bank shares this structure:

```
Record
  - record_id         : string   — unique identifier, auto-generated (used for deduplication)
  - source_type       : string   — "reddit" or "pdf"
  - source_id         : string   — subreddit name (e.g. "r/offmychest") or PDF filename
  - title             : string   — post title (Reddit) or nearest section heading (PDF)
  - text              : string   — full post body (Reddit) or extracted passage (PDF)
  - date_retrieved    : string   — ISO date format: YYYY-MM-DD
  - url               : string   — direct link to post (Reddit only; blank for PDF)
  - page_ref          : string   — page number or location (PDF only; blank for Reddit)
  - search_terms_used : string   — the search terms active during this retrieval run
  - stage_1           : blank    — manual coding field: antecedent meaning discrepancy
  - stage_2           : blank    — manual coding field: sudden meaning-making moment
  - stage_3           : blank    — manual coding field: narrative integration
  - overall_verdict   : blank    — manual coding field: pass / fail / ambiguous
  - notes             : blank    — free text field for researcher annotations
```

---

## 7. External Integrations

| Integration | Purpose | Credential Required |
|---|---|---|
| Reddit API (PRAW) | Retrieve posts from subreddits | Reddit account + free app registration |
| Anthropic Claude API | Extract candidate passages from PDF text | Existing API key |

### Deduplication Storage
- Method: JSON sidecar file (`seen_ids.json`)
- Location: lives in the same output folder as exports
- Behavior: auto-created on first run; updated after every run; deletable to reset the bank

---

## 8. Non-Functional Requirements

- **Privacy:** All data stays local. Only outbound calls are to Reddit API and Anthropic API.
- **Deduplication:** Persistent `seen_ids.json` tracks all previously retrieved `record_id` values and skips duplicates across runs.
- **Rate limiting:** Must respect Reddit API rate limits and handle rate limit errors gracefully without crashing.
- **Minimum post length:** Default threshold is 500 characters. Configurable in UI.
- **PDF robustness:** Handles standard text-based PDFs. Scanned/image-only PDFs are out of scope — tool must detect and surface a clear error message.
- **Error handling:** All errors surface as readable messages in the UI. No silent failures. No raw Python tracebacks shown to the user.
- **Performance:** Progress indicator for any operation expected to take more than 3 seconds.

---

## 9. Out of Scope — Version 1

- Automated prime-test scoring or AI judgment of any kind
- Hosting the tool online or making it accessible to other users
- Non-PDF file types (Word documents, web pages, plain text files)
- Any database — all storage is flat files (CSV + JSON)
- User accounts, login, or authentication
- Scheduled or automated runs
- Scanned PDF support (image-only PDFs with no embedded text)
- Multi-user collaboration or shared exports
- Built-in coding interface — annotation happens externally in Excel/Sheets

---

## 10. Open Questions

- Exact Claude prompt for PDF passage extraction — to be designed collaboratively during Slice 2
- Default subreddit list to pre-populate in the UI on first launch

# SLICE_2_REDDIT_SCRAPER.md
## Epiphany Narrative Example Bank — Retrieval Tool
*Slice 2 of 4: Reddit Scraper*

---

## Goal

Implement the Reddit scraper module and wire it to the UI so the user can retrieve full-text posts from a specified subreddit using configurable search terms, with results displayed in a preview table and exportable to CSV and JSON.

---

## Acceptance Criteria

1. Entering a valid subreddit URL and clicking "Run Reddit Scrape" retrieves posts and displays them in a results table
2. Each retrieved post contains all required fields: record_id, source_type, source_id, title, text, date_retrieved, url, page_ref, search_terms_used, plus blank coding fields (stage_1, stage_2, stage_3, overall_verdict, notes)
3. Posts shorter than the minimum length threshold are filtered out before display
4. The results table shows: source_id, title, first 200 characters of text, date_retrieved, url
5. Record count displays correctly: "X new records retrieved. Y total records in bank."
6. Clicking "Export CSV" appends new records to output/example_bank.csv and shows a success message
7. Clicking "Export JSON" appends new records to output/example_bank.json and shows a success message
8. Re-running the same search does not duplicate records — duplicate count shown: "X duplicates skipped."
9. A progress spinner shows while the scrape is running
10. If Reddit credentials are placeholders or invalid, a clear error message appears — not a raw Python traceback
11. If no posts are found matching the search terms, a clear "No results found" message appears
12. If the subreddit URL is malformed or the subreddit doesn't exist, a clear error message appears

---

## Files to Modify

```
MODIFY:   app.py                     — enable Reddit button, add scrape logic and results display
MODIFY:   modules/reddit_scraper.py  — full implementation
MODIFY:   modules/deduplicator.py    — full implementation
MODIFY:   modules/exporter.py        — full implementation
NO CHANGE: modules/pdf_processor.py  — leave completely untouched
```

---

## Record Schema

Every record must contain exactly these fields:

```
{
  "record_id":          "reddit_" + submission.id,
  "source_type":        "reddit",
  "source_id":          "r/" + subreddit_name,
  "title":              submission.title,
  "text":               submission.selftext,
  "date_retrieved":     YYYY-MM-DD string,
  "url":                submission.url,
  "page_ref":           "",
  "search_terms_used":  comma-joined search terms string,
  "stage_1":            "",
  "stage_2":            "",
  "stage_3":            "",
  "overall_verdict":    "",
  "notes":              ""
}
```

---

## Component Contracts

### modules/reddit_scraper.py
```
Function: scrape_subreddit(subreddit_url, search_terms, min_length)

- Parse subreddit name from any URL format (with/without https://, www., trailing slash)
- Initialize PRAW using env vars: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
- For each search term: call subreddit.search(term, limit=100)
- Filter out posts where len(selftext) < min_length
- Filter out posts where selftext is empty, "[removed]", or "[deleted]"
- Deduplicate within the current batch by submission.id before returning
- Return list of Record dicts
```

### modules/deduplicator.py
```
Function: filter_new(records) → list
- Load output/seen_ids.json on every call
- If file doesn't exist, treat as empty set
- Return only records whose record_id is not in seen_ids

Function: mark_seen(records) → None
- Load existing seen_ids.json
- Add all record_id values from records
- Write updated set back to seen_ids.json
- Create file if it doesn't exist
```

### modules/exporter.py
```
Function: export_records(records) → int
- Append to output/example_bank.csv (write header only if file doesn't exist yet)
- Append to output/example_bank.json (load existing array, append, write back)
- Return count of records written
- Never overwrite existing records
```

### app.py changes
```
- Enable "Run Reddit Scrape" button
- On click: show spinner, parse search terms, call scraper, filter duplicates,
  store in session_state, display results table, show counts
- Enable Export buttons when session_state has records
- On export: call exporter, call mark_seen, show success message
- All errors caught and shown via st.error() — no raw tracebacks
```

---

## Edge Cases to Handle

- Subreddit URL with trailing slash: strip cleanly
- Any URL format: with/without https://, www. — all parse correctly
- Post body is "[removed]" or "[deleted]": skip silently
- Reddit API rate limit hit: show "Rate limit reached — please wait 60 seconds and try again"
- Credentials still set to placeholder: show "Reddit credentials not configured. See REDDIT_API_SETUP.md."
- Subreddit is private or banned: show clear message
- Zero results after length filtering: show "No posts found matching your search terms. Try different terms or a lower minimum length."
- Network connection lost mid-scrape: show "Network error — check your connection and try again"

---

## Test Cases

1. Scrape r/offmychest with term "I realized" — posts appear in results table
2. Run same scrape again — "X duplicates skipped" message appears, no new records added
3. Enter a fake subreddit URL — clear error message appears
4. Set minimum length to 5000 — most posts filtered, low result count shown
5. Click Export CSV — file appears in output/ folder with correct columns
6. Click Export JSON — file appears in output/ folder with correct structure
7. Open exported CSV in Excel — all columns present including blank coding fields

---

## Codex Generation Prompt

```
CONTEXT:
I am building a local research tool called the Epiphany Narrative Example Bank Retrieval Tool — a Python + Streamlit web app that runs locally in the browser. The project folder is epiphany_scraper. Slice 1 (project scaffold) is complete — the app runs, the UI renders correctly, and all module stubs exist. This is Slice 2: implementing the Reddit scraper, deduplicator, and exporter modules, and wiring them to the UI.

TASK:
Implement the Reddit scraper, deduplicator, and exporter modules in full, and update app.py to wire them to the UI. The Reddit panel must go from a static disabled form to a fully working scraper that retrieves real posts, displays them in a preview table, and exports them to CSV and JSON.

FILES TO MODIFY:
1. app.py — enable Reddit button, add scrape logic, results display, and export handling
2. modules/reddit_scraper.py — full implementation using PRAW
3. modules/deduplicator.py — full implementation using seen_ids.json
4. modules/exporter.py — full implementation writing to CSV and JSON

DO NOT MODIFY:
- modules/pdf_processor.py — leave completely untouched
- requirements.txt — all packages already installed
- .env — never touch credentials files
- anything in the docs/ folder

CONSTRAINTS:
- Python 3.11+, Streamlit only for UI
- Use PRAW for all Reddit API calls
- Use python-dotenv — credentials loaded from .env only, never hardcoded
- Folder structure must remain exactly as established in Slice 1
- All errors must be caught and displayed via st.error() — no raw Python tracebacks ever shown to the user
- Use st.session_state to store retrieved records between interactions
- Export buttons must only be enabled when session_state contains records

RECORD SCHEMA — every record must contain exactly these fields:
{
  "record_id": "reddit_" + submission.id,
  "source_type": "reddit",
  "source_id": "r/" + subreddit_name,
  "title": submission.title,
  "text": submission.selftext,
  "date_retrieved": YYYY-MM-DD string,
  "url": submission.url,
  "page_ref": "",
  "search_terms_used": comma-joined search terms string,
  "stage_1": "",
  "stage_2": "",
  "stage_3": "",
  "overall_verdict": "",
  "notes": ""
}

REDDIT SCRAPER REQUIREMENTS (modules/reddit_scraper.py):
- Function signature: scrape_subreddit(subreddit_url: str, search_terms: list, min_length: int) -> list
- Parse subreddit name from any URL format: with or without https://, with or without www., with or without trailing slash
- Initialize PRAW using REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT from environment
- For each search term: call subreddit.search(term, limit=100)
- Filter out posts where len(selftext) < min_length
- Filter out posts where selftext is empty, "[removed]", or "[deleted]"
- Deduplicate within the current batch by submission.id before returning
- Return list of Record dicts

DEDUPLICATOR REQUIREMENTS (modules/deduplicator.py):
- filter_new(records: list) -> list: load output/seen_ids.json, return only records with unseen record_id values. If file doesn't exist treat as empty.
- mark_seen(records: list) -> None: load existing seen_ids.json, add new record_ids, write back. Create file if needed.

EXPORTER REQUIREMENTS (modules/exporter.py):
- export_records(records: list) -> int
- Append to output/example_bank.csv: write header only if file doesn't already exist
- Append to output/example_bank.json: load existing array if present, append new records, write full array back
- Return count of records written
- Never overwrite existing records

APP.PY CHANGES:
- Parse search terms: split input string by comma, strip whitespace from each term, remove empty strings
- Reddit button: enabled (remove disabled=True)
- On Reddit button click:
    - Wrap in try/except — catch all exceptions and show via st.error()
    - Show st.spinner("Retrieving posts from Reddit...")
    - Call scrape_subreddit() with parsed inputs
    - Call filter_new() to remove duplicates
    - Store results in st.session_state["records"]
    - Store duplicate count in st.session_state["duplicate_count"]
    - Display results using st.dataframe() showing columns: source_id, title, text preview (first 200 chars), date_retrieved, url
    - Show: "X new records retrieved. Y total records in bank."
    - If duplicates > 0 show: "X duplicates skipped."
    - If zero results after filtering: show st.info("No posts found matching your search terms.")
- Export CSV button: enabled only when st.session_state.get("records")
- Export JSON button: enabled only when st.session_state.get("records")
- On export click: call export_records(), call mark_seen(), show st.success("X records exported successfully.")
- PDF panel buttons remain disabled — do not change pdf_processor.py

ERROR MESSAGES TO HANDLE:
- PRAW authentication error (placeholder credentials): st.error("Reddit credentials not configured. Please complete setup in your .env file — see REDDIT_API_SETUP.md.")
- Subreddit not found / private / banned: st.error("Subreddit not found or is private. Check the URL and try again.")
- Rate limit exceeded: st.error("Reddit rate limit reached. Please wait 60 seconds and try again.")
- Any other exception: st.error(f"Unexpected error: {str(e)}")

ACCEPTANCE CRITERIA:
1. Entering a valid subreddit URL and clicking Run Reddit Scrape retrieves posts and displays them in a results table
2. Each record contains all fields from the schema above
3. Posts shorter than minimum length are filtered out
4. Results table shows source_id, title, text preview, date_retrieved, url
5. Record count and duplicate count messages display correctly
6. Export CSV creates/appends output/example_bank.csv with correct columns including blank coding fields
7. Export JSON creates/appends output/example_bank.json with correct structure
8. Re-running same search skips already-seen records and reports duplicate count
9. Progress spinner shows during scrape
10. All errors show as readable st.error() messages — no raw tracebacks

DO NOT:
- Modify modules/pdf_processor.py
- Hardcode any credentials
- Change the folder structure
- Add features outside this slice
- Show raw Python tracebacks to the user

OUTPUT:
Write the complete implementation for all modified files. Do not explain what you are doing — just produce the code. After writing, list any assumptions you made.
```

---

## Claude Code Debugging Prompt

```
CONTEXT:
I am building a local research tool called the Epiphany Narrative Example Bank Retrieval Tool — a Python + Streamlit web app. Slice 2 (Reddit scraper) was just generated by Codex. The Reddit panel should now retrieve real posts, display them in a results table, and export to CSV and JSON.

CURRENT PROBLEM:
[Describe exactly what isn't working — paste any error messages here]

RELEVANT FILES:
- app.py
- modules/reddit_scraper.py
- modules/deduplicator.py
- modules/exporter.py
- output/seen_ids.json (if it exists)

WHAT CODEX BUILT:
[Brief summary — e.g. "Scraper runs but returns empty results" or "Export button not appearing"]

CONSTRAINTS:
- Python 3.11+, Streamlit only for UI
- Do not modify modules/pdf_processor.py
- Do not refactor outside the scope of the current problem
- All errors must surface via st.error() — no raw tracebacks
- Maintain folder structure from ARCHITECTURE.md

ACCEPTANCE CRITERIA:
1. Run Reddit Scrape button retrieves real posts and displays results table
2. All record fields populated correctly including blank coding fields
3. Deduplication works across runs — duplicates skipped and counted
4. Export CSV and JSON write correct files to output/ folder
5. All errors shown as readable messages

DO NOT:
- Rewrite files that are working correctly
- Modify pdf_processor.py
- Add features outside this slice

OUTPUT:
Fix the problem described above. Summarize what was changed, why, and list follow-up issues for the next session.
```

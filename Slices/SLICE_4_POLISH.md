# SLICE_4_POLISH.md
## Epiphany Narrative Example Bank — Retrieval Tool
*Slice 4 of 4: UI Polish, Export Verification & Code Quality*

---

## Goal

Add the final UI improvements, verify the full export pipeline works end-to-end, and run a Claude Code polish pass across the entire codebase for code quality, elegance, and performance.

---

## Acceptance Criteria

### UI Features
1. A "Clear Session" button appears in the sidebar — clicking it clears current results from the UI without deleting any exported files or modifying seen_ids.json
2. A full text expander is available in the results table — clicking any row reveals the complete passage text
3. A session history panel appears in the sidebar showing which PDFs and subreddits have been processed in the current session
4. Session history updates correctly after each Reddit scrape and each PDF extraction

### Export Verification
5. Export CSV produces a file that opens correctly in Excel with all 14 columns present and blank coding fields visible
6. Export JSON produces a well-formed JSON file with correct structure
7. Exported records from both Reddit and PDF sources appear correctly in the same file
8. Re-exporting after a Clear Session does not duplicate records

### Living Documentation
9. docs/CHANGELOG.md exists and documents all four slices
10. docs/DECISIONS.md exists and documents key architectural decisions
11. docs/KNOWN_ISSUES.md is up to date with all flagged items

### Code Quality
12. All modules pass Claude Code review for elegance, readability, and performance
13. No redundant code, unused imports, or inconsistent patterns across modules
14. Error handling is consistent across all modules

---

## Files to Create or Modify

```
MODIFY:  app.py                  — Clear Session button, full text expander, session history
CREATE:  docs/CHANGELOG.md       — living changelog
CREATE:  docs/DECISIONS.md       — architectural decisions log
UPDATE:  docs/KNOWN_ISSUES.md    — update with all known items
ALL FILES — Claude Code polish pass after Codex builds new features
```

---

## Component Contracts

### Clear Session Button
```
- Location: sidebar, below Environment Status
- Label: "Clear Session"
- Only show when records are present
- On click:
    - Clear st.session_state["records"]
    - Clear st.session_state["duplicate_count"]
    - Clear st.session_state["session_history"]
    - Do NOT modify output/ files
    - Do NOT modify seen_ids.json
    - Show st.sidebar.success("Session cleared.")
    - Call st.rerun()
```

### Full Text Expander
```
- Renders below results dataframe
- Only renders when records are present
- st.subheader("Full Passage Text")
- For each record:
    - label = title[:60] + " — " + date_retrieved
    - st.expander(label):
        - st.write(record["text"])
        - st.caption: source_id, url (if present), page_ref (if present)
```

### Session History Panel
```
- Location: sidebar, below Clear Session button
- Only renders when session_history is not empty
- st.sidebar.subheader("This Session")
- Each item rendered as st.sidebar.caption()
- After Reddit scrape: append "r/subredditname — X records"
- After PDF extraction: append "filename.pdf — X records"
- Clear Session resets to []
```

---

## Export Verification Test Protocol

Run these steps manually and confirm each:

1. Drop in a PDF → Run PDF Extraction → Export CSV
   - Open output/example_bank.csv in Excel or Google Sheets
   - Confirm all 14 column headers present
   - Confirm coding fields (stage_1, stage_2, stage_3, overall_verdict, notes) are blank
   - Confirm text field contains full passage text

2. Export JSON → open output/example_bank.json in VS Code
   - Confirm valid JSON array
   - Confirm each record has all 14 fields

3. Click Clear Session → click Export CSV again
   - Confirm no duplicate rows added

---

## Codex Generation Prompt

```
CONTEXT:
I am building a local research tool called the Epiphany Narrative Example Bank Retrieval Tool — a Python + Streamlit web app. The project folder is epiphany_scraper. Slices 1, 2, and 3 are complete — the scaffold, Reddit scraper, and PDF processor are all working. This is Slice 4: the final UI polish slice adding a Clear Session button, full text expander, and session history panel.

TASK:
Add three UI features to app.py: a Clear Session button in the sidebar, a full text expander below the results table, and a session history panel in the sidebar. Do not touch any module files — all changes are in app.py only.

FILES TO MODIFY:
1. app.py — add Clear Session button, full text expander, session history panel

DO NOT MODIFY:
- modules/reddit_scraper.py
- modules/pdf_processor.py
- modules/deduplicator.py
- modules/exporter.py
- requirements.txt
- .env
- anything in docs/ or prompts/

CONSTRAINTS:
- Python 3.11+, Streamlit only for UI
- All new features use st.session_state — no external state files
- Clear Session must not touch output/ files or seen_ids.json
- Session history must update after every scrape and extraction run
- Full text expander must render below the results dataframe

CLEAR SESSION BUTTON:
- Location: st.sidebar, below Environment Status section
- Label: "Clear Session"
- On click:
    - Set st.session_state["records"] = []
    - Set st.session_state["duplicate_count"] = 0
    - Set st.session_state["session_history"] = []
    - Show st.sidebar.success("Session cleared.")
    - Call st.rerun()
- Only show button when st.session_state.get("records") is not empty

FULL TEXT EXPANDER:
- Render below the results st.dataframe()
- Only render when st.session_state.get("records") is not empty
- st.subheader("Full Passage Text")
- For each record in st.session_state["records"]:
    - label = record["title"][:60] + " — " + record["date_retrieved"]
    - st.expander(label):
        - st.write(record["text"])
        - st.caption(f"Source: {record['source_id']}")
        - If record["url"]: st.caption(f"URL: {record['url']}")
        - If record["page_ref"]: st.caption(f"Page: {record['page_ref']}")

SESSION HISTORY PANEL:
- Location: st.sidebar, below Clear Session button
- Only render when st.session_state.get("session_history") is not empty
- st.sidebar.subheader("This Session")
- Render each item in st.session_state["session_history"] as st.sidebar.caption()
- Initialize st.session_state["session_history"] = [] if not present
- After successful Reddit scrape: append f"r/{subreddit_name} — {len(new_records)} records"
- After successful PDF extraction: append f"{filename} — {len(new_records)} records"
- Clear Session resets session_history to []

ACCEPTANCE CRITERIA:
1. Clear Session button appears in sidebar when results are present, clears UI without touching output files
2. Full text expander renders below results table with complete passage text for each record
3. Session history panel updates correctly after each run
4. All existing functionality from Slices 1-3 continues to work correctly

DO NOT:
- Modify any module files
- Add features outside this scope
- Change the folder structure
- Break any existing Slice 2 or Slice 3 functionality

OUTPUT:
Write the complete updated app.py. Do not explain what you are doing — just produce the code. After writing, list any assumptions you made.
```

---

## Claude Code Polish Prompt — Full Codebase

Run this after Codex finishes and the new features are verified working.

```
CONTEXT:
I have built a local research tool called the Epiphany Narrative Example Bank Retrieval Tool — a Python + Streamlit web app in a folder called epiphany_scraper. The tool is functionally complete across 4 slices. I now want a full codebase review and polish pass focused equally on code quality/elegance and performance.

FILES TO REVIEW AND IMPROVE:
- app.py
- modules/reddit_scraper.py
- modules/pdf_processor.py
- modules/exporter.py
- modules/deduplicator.py

POLISH PRIORITIES — equally weighted:
1. Code quality and elegance:
   - Remove unused imports
   - Eliminate redundant code and repeated patterns
   - Improve naming — variables, functions, and parameters should be clear and consistent
   - Ensure consistent error handling patterns across all modules
   - Ensure consistent return types and docstrings across all modules
   - Simplify overly complex logic where simpler approaches exist

2. Performance:
   - Identify any unnecessary repeated file reads (e.g. seen_ids.json read multiple times)
   - Improve chunking logic in pdf_processor.py if it can be made more efficient
   - Ensure session_state is used efficiently in app.py — no unnecessary reruns
   - Identify any blocking operations that could be made more responsive

CONSTRAINTS:
- Do not change any function signatures called from app.py
- Do not change the folder structure
- Do not modify requirements.txt
- Do not touch .env or prompts/pdf_extraction_prompt.txt
- Do not add new features — polish pass only
- All existing functionality must continue to work after changes

OUTPUT:
Make all improvements across the files listed. After making changes produce a summary organized as:
1. Changes made per file — what changed and why
2. Performance improvements identified and applied
3. Issues outside scope of polish pass — log as recommendations for future improvement
```

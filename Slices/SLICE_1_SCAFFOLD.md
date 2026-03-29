# SLICE_1_SCAFFOLD.md
## Epiphany Narrative Example Bank — Retrieval Tool
*Slice 1 of 4: Project Scaffold*

---

## Goal

Set up the complete project structure, install all dependencies, and get a Streamlit app running locally in the browser with the correct two-panel UI layout and placeholder content.

---

## Acceptance Criteria

1. Running `streamlit run app.py` in Terminal launches the app and opens it in the browser without errors
2. The UI displays two clearly separated panels — Reddit Panel on the left, PDF Panel on the right
3. The Reddit Panel contains: a text input for subreddit URL, a text input for search terms, a number input for minimum post length, and a disabled "Run Reddit Scrape" button
4. The PDF Panel contains: a file uploader accepting PDF files only, and a disabled "Run PDF Extraction" button
5. A results area appears below both panels with placeholder text: "No results yet. Run a scrape or upload a PDF to get started."
6. Export CSV and Export JSON buttons appear in the results area but are disabled
7. The app reads from `.env` successfully — confirmed by a green status indicator in the sidebar showing "Environment: Ready"
8. If any required environment variable is missing from `.env`, the sidebar shows a red indicator with the name of the missing variable
9. All five modules exist as empty files with correct placeholder structure
10. `requirements.txt` is present and contains all five dependencies

---

## Files to Create

```
epiphany-tool/
├── .env                        (create manually — not by Codex)
├── .gitignore
├── requirements.txt
├── README.md
├── app.py
├── modules/
│   ├── __init__.py
│   ├── reddit_scraper.py
│   ├── pdf_processor.py
│   ├── exporter.py
│   └── deduplicator.py
├── prompts/
│   └── pdf_extraction_prompt.txt
└── output/
    └── .gitkeep
```

---

## Component Contracts

### app.py structure
```
- Load environment variables via python-dotenv on startup
- Check for all four required env vars
- Render sidebar with environment status indicator
- Render two-column layout: Reddit Panel (left) | PDF Panel (right)
- Render results area below both panels
- All action buttons disabled (enabled in later slices)
- Import all four modules
```

### Module stubs
```
Each file contains:
- A module-level docstring describing its single responsibility
- Placeholder function signatures with correct names and parameters
- Each function body returns None or empty list
- No implementation logic
```

---

## Required Function Signatures

```
modules/reddit_scraper.py:
  def scrape_subreddit(subreddit_url: str, search_terms: list, min_length: int) -> list

modules/pdf_processor.py:
  def process_pdf(file_path: str) -> list

modules/exporter.py:
  def export_records(records: list) -> int

modules/deduplicator.py:
  def filter_new(records: list) -> list
  def mark_seen(records: list) -> None
```

---

## Edge Cases to Handle

- If `.env` file doesn't exist: show red error in sidebar — "Missing .env file. See REDDIT_API_SETUP.md."
- If `.env` exists but a variable is blank: show which specific variable is missing by name
- If `output/` folder doesn't exist: create it automatically on startup

---

## Test Cases

1. Run `streamlit run app.py` — browser opens, no Python errors in Terminal
2. Remove one variable from `.env` — red indicator appears naming the missing variable
3. Restore `.env` — green indicator returns
4. Upload a non-PDF file to the PDF uploader — Streamlit rejects it automatically

---

## Codex Generation Prompt

```
CONTEXT:
I am building a local research tool called the Epiphany Narrative Example Bank Retrieval Tool. It is a Python + Streamlit web app that runs locally in the browser. The tool has two modules: a Reddit scraper (using PRAW) and a PDF processor (using PyMuPDF and the Anthropic Claude API). This is Slice 1 — the project scaffold. No Reddit or PDF logic is being built yet. The goal is a clean, running app with the correct structure and UI skeleton.

TASK:
Create the complete project scaffold for this app. This includes the folder structure, all dependency files, a working Streamlit UI with the correct two-panel layout, and empty module stubs. The app must run without errors and display the correct UI immediately.

FILES TO CREATE:
1. app.py — main Streamlit application entry point
2. modules/__init__.py — empty file, makes modules a Python package
3. modules/reddit_scraper.py — stub module, Reddit scraping logic goes here later
4. modules/pdf_processor.py — stub module, PDF processing logic goes here later
5. modules/exporter.py — stub module, CSV/JSON export logic goes here later
6. modules/deduplicator.py — stub module, deduplication logic goes here later
7. prompts/pdf_extraction_prompt.txt — placeholder text only for now
8. output/.gitkeep — empty file to preserve the output folder in Git
9. requirements.txt — all project dependencies with pinned versions
10. .gitignore — ignore .env, output/*.csv, output/*.json, output/seen_ids.json, __pycache__, .DS_Store
11. README.md — basic setup and run instructions

CONSTRAINTS:
- Python 3.11+
- Streamlit for all UI — no HTML, CSS, or JavaScript
- Use python-dotenv to load environment variables from .env
- Follow this exact folder structure: app.py at root, all modules in modules/, prompt in prompts/, exports in output/
- Use Streamlit's st.columns() for the two-panel layout
- All action buttons must be rendered as disabled using the disabled=True parameter
- Do not implement any Reddit, PDF, or export logic — stubs only
- Module stubs must contain correct function signatures as specified below

REQUIRED FUNCTION SIGNATURES:
modules/reddit_scraper.py:
  def scrape_subreddit(subreddit_url: str, search_terms: list, min_length: int) -> list:

modules/pdf_processor.py:
  def process_pdf(file_path: str) -> list:

modules/exporter.py:
  def export_records(records: list) -> int:

modules/deduplicator.py:
  def filter_new(records: list) -> list:
  def mark_seen(records: list) -> None:

ENVIRONMENT VARIABLE HANDLING in app.py:
- Required variables: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, ANTHROPIC_API_KEY
- On startup: check all four variables are present and non-empty
- Render a sidebar section titled "Environment Status"
- If all variables present: st.sidebar.success("Environment: Ready")
- If .env file missing or any variable absent: st.sidebar.error("Missing: [VARIABLE_NAME]") for each missing variable
- Create output/ directory automatically if it does not exist

UI LAYOUT REQUIREMENTS:
app.py must render exactly this layout:
  - Page title: "Epiphany Narrative Example Bank"
  - Page subtitle: "Retrieve and export candidate epiphanic accounts for manual coding"
  - Two columns side by side:
    LEFT COLUMN — "Reddit Scraper":
      - st.text_input: label "Subreddit URL", placeholder "https://www.reddit.com/r/offmychest"
      - st.text_input: label "Search Terms (comma-separated)", value "I realized, it hit me, that moment, everything changed, it clicked"
      - st.number_input: label "Minimum Post Length (characters)", min_value=100, value=500
      - st.button: "Run Reddit Scrape", disabled=True
    RIGHT COLUMN — "PDF Processor":
      - st.file_uploader: label "Drop a PDF here", type=["pdf"]
      - st.button: "Run PDF Extraction", disabled=True
  - Results section below columns:
      - st.subheader: "Results"
      - st.info: "No results yet. Run a scrape or upload a PDF to get started."
      - Two side-by-side buttons: "Export CSV" and "Export JSON", both disabled=True

REQUIREMENTS.TXT must contain exactly:
streamlit==1.32.0
praw==7.7.1
pymupdf==1.24.0
anthropic==0.21.0
python-dotenv==1.0.0

ACCEPTANCE CRITERIA:
1. Running "streamlit run app.py" launches without errors
2. UI displays correct two-panel layout with all specified inputs and buttons
3. Sidebar shows environment status correctly based on .env contents
4. All buttons are disabled
5. Results area shows placeholder message
6. All module stubs exist with correct function signatures
7. requirements.txt contains all five dependencies
8. output/ directory is created automatically if missing

DO NOT:
- Modify any files outside the list above
- Add features outside the scope of this slice
- Implement any Reddit, PDF, or export logic
- Leave placeholder comments or TODOs — implement fully or omit
- Use any UI framework other than Streamlit

OUTPUT:
Write the complete implementation for all files listed above. Do not explain what you are doing — just produce the code. After writing, list any assumptions you made.
```

---

## Claude Code Debugging Prompt

```
CONTEXT:
I am building a local research tool called the Epiphany Narrative Example Bank Retrieval Tool — a Python + Streamlit web app. Slice 1 (project scaffold) was just generated by Codex. The app should run with "streamlit run app.py" and display a two-panel UI with disabled controls and an environment status sidebar.

CURRENT PROBLEM:
[Describe exactly what isn't working — paste any error messages from Terminal here]

RELEVANT FILES:
- app.py
- modules/__init__.py
- modules/reddit_scraper.py
- modules/pdf_processor.py
- modules/exporter.py
- modules/deduplicator.py
- requirements.txt
- .env

WHAT CODEX BUILT:
[Brief summary — e.g. "All files were created. App launches but sidebar status indicator is not showing" or "Import error on startup"]

CONSTRAINTS:
- Python 3.11+, Streamlit only for UI
- Do not refactor outside the scope of the current problem
- Do not implement Reddit, PDF, or export logic — stubs only
- Maintain the folder structure from ARCHITECTURE.md

ACCEPTANCE CRITERIA:
1. Running "streamlit run app.py" launches without errors
2. Two-panel UI displays correctly with all inputs and disabled buttons
3. Sidebar shows green "Environment: Ready" when all .env variables are present
4. Sidebar shows red error naming each missing variable when any are absent
5. All module stubs exist with correct function signatures

DO NOT:
- Rewrite files that are working correctly
- Add features outside this slice
- Change the folder structure

OUTPUT:
Fix the problem described above. After making changes, summarize exactly what was changed, why, and list any follow-up issues for the next session.
```

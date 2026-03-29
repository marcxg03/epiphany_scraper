# ARCHITECTURE.md
## Epiphany Narrative Example Bank — Retrieval Tool
*Version 1.0*

---

## 1. Tech Stack

| Layer | Tool | What It Is | Why We're Using It |
|---|---|---|---|
| Language | Python 3.11+ | The programming language everything is written in | Best ecosystem for research tools, APIs, and data processing |
| UI Framework | Streamlit | A Python library that turns a script into a local web app | Fastest path from Python to a working browser UI; used widely in research and data science |
| Reddit API Client | PRAW | "Python Reddit API Wrapper" — handles all Reddit API communication | Official, well-documented standard for Reddit access in Python |
| PDF Text Extraction | PyMuPDF (fitz) | Reads PDF files and extracts all text | Handles all PDF types reliably; fast and well-maintained |
| AI Passage Extraction | Anthropic Python SDK | Official library for talking to Claude's API from Python | Existing API key; Claude is well-suited for identifying narrative passages in unstructured text |
| Data Export | Python csv + json | Built into Python — no installation needed | Simple, reliable, zero dependencies |
| Dependency Management | pip + requirements.txt | pip is Python's package installer; requirements.txt lists everything the project needs | Standard, beginner-friendly, works out of the box on Mac |
| Environment Variables | python-dotenv | Reads your `.env` file and makes credentials available to the app | Keeps credentials out of your code; standard practice for API key projects |

---

## 2. File and Folder Structure

```
epiphany-tool/
│
├── .env                          # Your private credentials — never shared or uploaded
├── .gitignore                    # Tells Git to ignore .env and output files
├── requirements.txt              # List of all Python packages needed to run the app
├── README.md                     # Setup instructions for running the tool
│
├── app.py                        # Main entry point — launches the Streamlit UI
│
├── modules/
│   ├── __init__.py               # Makes 'modules' a Python package (empty file, required)
│   ├── reddit_scraper.py         # All Reddit API logic — search, retrieve, filter
│   ├── pdf_processor.py          # All PDF logic — extract text, send to Claude, parse response
│   ├── exporter.py               # All export logic — write CSV and JSON output files
│   └── deduplicator.py           # All deduplication logic — read/write seen_ids.json
│
├── prompts/
│   └── pdf_extraction_prompt.txt # The Claude prompt for identifying epiphanic passages
│
├── output/
│   ├── example_bank.csv          # Your growing CSV export — appended after each run
│   ├── example_bank.json         # Your growing JSON export — appended after each run
│   └── seen_ids.json             # Deduplication log — tracks all retrieved record IDs
│
└── docs/
    ├── PROJECT_BRIEF.md          # From Phase 0
    ├── MASTER_SPEC.md            # From Phase 1
    ├── ARCHITECTURE.md           # This document
    ├── REDDIT_API_SETUP.md       # Reddit credential setup guide
    ├── CHANGELOG.md              # Updated after each slice is built
    ├── DECISIONS.md              # Architectural decisions log
    └── KNOWN_ISSUES.md           # Bugs and limitations log
```

---

## 3. Module Map

Each module has exactly one job.

| Module | Single Responsibility |
|---|---|
| `app.py` | Renders the Streamlit UI; calls modules in response to user actions; displays results |
| `reddit_scraper.py` | Connects to Reddit API via PRAW; searches subreddit by query terms; filters by length; returns structured records |
| `pdf_processor.py` | Accepts a PDF file; extracts full text via PyMuPDF; sends text to Claude API with extraction prompt; parses and returns candidate passages as structured records |
| `exporter.py` | Accepts a list of records; appends to `example_bank.csv` and `example_bank.json`; never overwrites existing data |
| `deduplicator.py` | Reads `seen_ids.json` on startup; checks new records against seen IDs; writes new IDs back after each run |

---

## 4. Data Flow

### Reddit Flow
```
User pastes subreddit URL + search terms
        ↓
app.py calls reddit_scraper.py
        ↓
reddit_scraper.py queries Reddit API → retrieves matching posts → filters by length
        ↓
reddit_scraper.py returns list of raw records
        ↓
app.py passes records to deduplicator.py → removes already-seen records
        ↓
app.py displays new records in preview table
        ↓
User clicks Export → app.py calls exporter.py
        ↓
exporter.py appends to example_bank.csv + example_bank.json
deduplicator.py updates seen_ids.json
```

### PDF Flow
```
User drops PDF file into UI
        ↓
app.py calls pdf_processor.py
        ↓
pdf_processor.py extracts full text via PyMuPDF
        ↓
pdf_processor.py sends text to Claude API with extraction prompt
        ↓
Claude returns list of candidate passages
        ↓
pdf_processor.py parses response → returns structured records
        ↓
app.py passes records to deduplicator.py → removes already-seen records
        ↓
app.py displays new records in preview table
        ↓
User clicks Export → app.py calls exporter.py
        ↓
exporter.py appends to example_bank.csv + example_bank.json
deduplicator.py updates seen_ids.json
```

---

## 5. API Contracts

### reddit_scraper.py
```
Function: scrape_subreddit(subreddit_url, search_terms, min_length)

Input:
  - subreddit_url  : string  — e.g. "https://www.reddit.com/r/offmychest"
  - search_terms   : list    — e.g. ["I realized", "it hit me", "that moment"]
  - min_length     : int     — minimum character count, e.g. 500

Output:
  - list of Record dicts, each containing all fields from the data model
  - empty list if no results found
  - raises RedditAPIError with readable message if API call fails
```

### pdf_processor.py
```
Function: process_pdf(file_path)

Input:
  - file_path : string — path to the uploaded PDF file

Output:
  - list of Record dicts, each containing all fields from the data model
  - empty list if no passages identified
  - raises PDFExtractionError with readable message if:
      - file is not a valid PDF
      - PDF contains no extractable text (scanned/image-only)
      - Claude API call fails
```

### exporter.py
```
Function: export_records(records)

Input:
  - records : list of Record dicts

Output:
  - appends to output/example_bank.csv
  - appends to output/example_bank.json
  - returns count of records written
  - never overwrites existing records
```

### deduplicator.py
```
Function: filter_new(records) → list
Function: mark_seen(records) → None

filter_new Input:  list of Record dicts
filter_new Output: list with already-seen records removed

mark_seen Input:   list of Record dicts
mark_seen Output:  updates seen_ids.json with new record_id values
```

---

## 6. Environment Variables

All credentials live in `.env` and are never hardcoded into any Python file.

```
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=epiphany-research-tool by u/your_reddit_username
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

---

## 7. Key Dependencies

```
streamlit==1.32.0
praw==7.7.1
pymupdf==1.24.0
anthropic==0.21.0
python-dotenv==1.0.0
```

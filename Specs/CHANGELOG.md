# CHANGELOG.md
## Epiphany Narrative Example Bank — Retrieval Tool

---

## Slice 4 — UI Polish & Code Quality
*Status: In progress*

### Added
- Clear Session button in sidebar — discards current results without modifying exported files
- Full text expander below results table — click any record to read complete passage
- Session history panel in sidebar — tracks which sources were processed this session

### Changed
- Full codebase polish pass — improved code quality, consistency, and performance across all modules

---

## Slice 3 — PDF Processor
*Status: Complete*

### Added
- modules/pdf_processor.py — full implementation using PyMuPDF and Anthropic SDK
- prompts/pdf_extraction_prompt.txt — Claude extraction prompt grounded in epiphanic sequence theory
- PDF file drop zone in UI now functional
- Long PDF chunking — PDFs over 15,000 characters chunked into sections for API calls

### Changed
- app.py — PDF panel enabled, extraction logic wired to results display and export system
- prompts/pdf_extraction_prompt.txt — updated with form requirement filter (first-person narrative only)

### Fixed
- anthropic==0.21.0 / httpx version conflict — pinned httpx>=0.23.0,<0.28.0 in requirements.txt
- Model ID corrected from claude-sonnet-4-20250514 to claude-sonnet-4-6

---

## Slice 2 — Reddit Scraper
*Status: Complete*

### Added
- modules/reddit_scraper.py — full PRAW implementation
- modules/deduplicator.py — seen_ids.json based deduplication
- modules/exporter.py — CSV and JSON export with append behavior
- Reddit panel fully functional — scrape, deduplicate, preview, export

### Fixed
- Export double-click bug — records cleared from session after export to prevent duplicate rows
- ValueError handler — malformed URLs now surface clean error messages instead of "Unexpected error"

---

## Slice 1 — Project Scaffold
*Status: Complete*

### Added
- Complete project folder structure
- app.py — Streamlit UI skeleton with two-panel layout
- All module stubs with correct function signatures
- requirements.txt with all five dependencies
- .gitignore — protects .env and output files from Git
- README.md — setup and run instructions
- Environment status indicator in sidebar

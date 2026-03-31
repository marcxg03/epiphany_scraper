# KNOWN_ISSUES.md
## Epiphany Narrative Example Bank — Retrieval Tool

---

## Open Issues

### KI-001 — Reddit credentials pending API approval
**Slice:** 2
**Description:** Reddit API registration submitted for academic researcher access. Reddit scraper is fully built but cannot retrieve live data until approval email arrives and real credentials are added to .env.
**Status:** Pending — waiting on Reddit approval email
**Resolution:** Add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to .env when credentials arrive

---

### KI-002 — System-level ANTHROPIC_API_KEY overrides .env
**Slice:** 3
**Description:** If ANTHROPIC_API_KEY is set as a system environment variable (e.g. via shell config), it overrides the value in .env. This caused repeated 401 authentication errors during development.
**Status:** Open — workaround in place
**Workaround:** Run `export ANTHROPIC_API_KEY=your_key` in Terminal before launching app, or ensure .zshrc contains the correct key value
**Future fix:** Upgrade to anthropic>=0.40.0 and audit shell environment for stale key exports

---

### KI-003 — anthropic==0.21.0 requires httpx pin
**Slice:** 3
**Description:** anthropic==0.21.0 is incompatible with httpx>=0.28.0. Fixed by pinning httpx>=0.23.0,<0.28.0 in requirements.txt.
**Status:** Resolved with pin — monitor for future conflicts
**Future fix:** Upgrade to anthropic>=0.40.0 which drops the proxies usage, then remove the httpx pin

---

### KI-004 — PDF chunking splits mid-sentence at 15k character boundary
**Slice:** 3
**Description:** Passages near chunk boundaries may be truncated. Claude processes each chunk independently so cross-boundary passages may be missed or split.
**Status:** Open — acceptable for V1 candidate retrieval
**Future fix:** Implement sentence-aware chunking using a text splitter

---

### KI-005 — Results table text preview truncates at 200 characters
**Slice:** 3
**Description:** The results dataframe shows only the first 200 characters of each passage.
**Status:** Resolved in Slice 4 — full text expander added below results table

---

### KI-006 — PDF source_id and title include file extension
**Slice:** 3
**Description:** source_id and title are set to the raw filename including .pdf extension. Cosmetically could be cleaner.
**Status:** Open — cosmetic, low priority
**Future fix:** Strip extension from title field in pdf_processor.py

---

### KI-007 — Scanned PDF support not available
**Slice:** 3
**Description:** PDFs containing only scanned images with no embedded text are not supported. Tool detects this and shows a clean error message.
**Status:** Open — explicitly out of scope for V1
**Future fix:** Integrate OCR library (pytesseract or similar) for scanned PDF support in V2

---

## Resolved Issues

| ID | Description | Resolution |
|---|---|---|
| KI-005 | Results table truncates at 200 chars | Full text expander added in Slice 4 |
| httpx conflict | anthropic SDK incompatible with httpx>=0.28 | Pinned httpx in requirements.txt |
| Model ID | Codex used invalid model ID | Claude Code corrected to claude-sonnet-4-6 |
| Export double-click | Second export click duplicated rows | Session cleared after export in app.py |
| ValueError handler | Malformed URLs showed "Unexpected error" | Added specific ValueError catch in app.py |

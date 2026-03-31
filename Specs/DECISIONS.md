# DECISIONS.md
## Epiphany Narrative Example Bank — Retrieval Tool
*Key architectural decisions and rationale*

---

## D-001 — Streamlit as UI framework
**Decision:** Use Streamlit rather than a full web framework (Flask, FastAPI + React)
**Rationale:** Single researcher, local tool, beginner codebase. Streamlit provides a working browser UI from pure Python with no HTML/CSS/JS required. Eliminates an entire layer of complexity that would add no research value.
**Tradeoff:** Less UI flexibility than a custom frontend. Acceptable for a single-user research tool.

---

## D-002 — Flat file output (CSV + JSON) over database
**Decision:** Write exports to flat files rather than SQLite or any database
**Rationale:** Output is consumed externally in Excel/Google Sheets for manual coding. Flat files are directly openable without any tooling. A database would add complexity with no benefit for a single researcher workflow.
**Tradeoff:** No querying capability within the tool. Acceptable — querying happens in Excel.

---

## D-003 — JSON sidecar file for deduplication
**Decision:** Track seen record IDs in a separate seen_ids.json file rather than checking the export files directly
**Rationale:** Checking export files for duplicates would require reading and parsing potentially large CSV/JSON files on every run. A dedicated ID store is fast, simple, and deletable to reset the bank.
**Tradeoff:** Two sources of truth (export files + seen_ids.json) that can theoretically diverge if files are manually edited. Acceptable for single-researcher use.

---

## D-004 — Claude API for PDF passage extraction (not keyword search)
**Decision:** Use Claude to identify candidate passages rather than keyword/regex search
**Rationale:** Epiphanic sequences are defined by narrative structure and meaning-making quality, not by surface keywords. A keyword approach would produce high false-positive rates and miss structurally valid passages that don't use expected vocabulary. Claude's reading comprehension is necessary for construct-valid retrieval.
**Tradeoff:** API cost per PDF processed. Acceptable at research scale.

---

## D-005 — Extraction prompt: form filter before content evaluation
**Decision:** Add a first-person narrative form requirement as a pre-filter before epiphanic content evaluation in the Claude prompt
**Rationale:** Initial testing showed Claude extracting analytical and third-person descriptive passages that satisfied thematic criteria but were not narrative accounts. The form filter (first-person, narrative arc, lived experience voice) is a necessary precondition for the epiphanic coding scheme to apply.
**Tradeoff:** May exclude some valid embedded narratives in academic texts. Acceptable — the prompt explicitly allows quoted first-person speech within larger texts.

---

## D-006 — httpx version pin
**Decision:** Pin httpx>=0.23.0,<0.28.0 in requirements.txt
**Rationale:** anthropic==0.21.0 passes a proxies argument to httpx.Client.__init__() which was removed in httpx==0.28.0. Without the pin, pip installs the latest httpx and breaks the SDK silently.
**Future:** Upgrade to anthropic>=0.40.0 which drops the proxies usage entirely, then remove the httpx pin.

---

## D-007 — One Anthropic API key across projects
**Decision:** Use a single Anthropic API key shared across projects rather than strictly isolated per-project keys
**Rationale:** API keys are organizational labels, not security boundaries between personal projects. A single key simplifies credential management for a solo researcher.
**Note:** System-level ANTHROPIC_API_KEY in shell environment overrides .env file values. Set via export in .zshrc or use export command in Terminal session to ensure correct key is active.

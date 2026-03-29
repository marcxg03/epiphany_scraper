# Project Brief
## Epiphany Narrative Example Bank — Retrieval Tool
*Version 1.0*

---

## What This Is

A local web application that runs in your browser on your own computer. It has two jobs:
1. Retrieve first-person narrative posts from Reddit subreddits you specify
2. Extract candidate passages from PDF documents you drop in

Both jobs produce the same structured output — a set of candidate epiphanic accounts ready for manual prime-test coding — exported to CSV and JSON for review in Excel or Google Sheets.

---

## The Problem It Solves

Manually collecting first-person narrative accounts for epiphanic sequence coding is slow, unsystematic, and difficult to scale. This tool automates the retrieval and extraction step across two source types — Reddit posts and PDF documents — producing a unified, consistently structured candidate bank ready for manual prime-test coding.

---

## Who Uses It

**Primary user:** A single graduate researcher running the tool locally on a personal Mac.

**Technical level:** Beginner. The tool must be runnable without command-line interaction after initial setup. All inputs and controls live in the browser UI.

---

## What Success Looks Like

You can:
- Paste a subreddit URL into the tool, set your search terms, and retrieve a batch of candidate posts
- Drop a PDF into the tool and receive extracted candidate passages from it
- Export all results to CSV and JSON with consistent fields across both sources
- Re-run the tool with new inputs without duplicating records already collected
- Manually apply your prime-test coding scheme to the exported file in Excel or Sheets

---

## Two Core Modules

**Module 1 — Reddit Scraper**
- Input: subreddit URL (pasted into UI) + search terms (editable in UI)
- Process: query Reddit API, retrieve full post text, filter by minimum length
- Output: structured records with source, post ID, title, body, date retrieved, blank coding fields

**Module 2 — PDF Processor**
- Input: PDF file dropped into UI (books, articles, transcripts, memoirs, etc.)
- Process: extract full text, send to Claude API with instructions to identify candidate epiphanic passages
- Output: structured records with source filename, passage text, page reference where possible, blank coding fields

---

## Shared Output Fields

Every record — regardless of source — will have:

| Field | Description |
|---|---|
| `source_type` | "reddit" or "pdf" |
| `source_id` | Subreddit name or PDF filename |
| `record_id` | Unique identifier for deduplication |
| `title` | Post title (Reddit) or document section heading (PDF) |
| `text` | Full post body or extracted passage |
| `date_retrieved` | When the tool retrieved it |
| `url` | Direct link to post (Reddit only; blank for PDF) |
| `page_ref` | Page number or location (PDF only; blank for Reddit) |
| `search_terms_used` | The search terms active during this retrieval run |
| `stage_1` | Blank — manual coding field |
| `stage_2` | Blank — manual coding field |
| `stage_3` | Blank — manual coding field |
| `overall_verdict` | Blank — manual coding field |
| `notes` | Blank — free text field for researcher annotations |

---

## Tech Stack

| Layer | Tool | Reason |
|---|---|---|
| Language | Python | Stated preference; excellent library support |
| UI Framework | Streamlit | Turns a Python script into a local web app with minimal code |
| Reddit API | PRAW | Standard Python library for Reddit; well-documented |
| PDF Processing | PyMuPDF | Reliable text extraction across all PDF types |
| AI Extraction | Claude API (Anthropic) | Identifies candidate passages from PDF text |
| Output | CSV + JSON | Via Python's built-in libraries |

---

## Out of Scope — Version 1

- Automated prime-test scoring or AI judgment of any kind
- Hosting the tool online or sharing with other users
- Non-PDF file types (Word documents, web pages, plain text files)
- Any database — flat file output only
- User accounts, login, or authentication
- Scheduled or automated runs
- Scanned PDF support (image-only PDFs with no embedded text)
- Multi-user collaboration or shared exports
- Built-in coding interface — annotation happens externally in Excel/Sheets

---

## Pre-Run Setup Checklist

Before running the tool for the first time:

1. Confirm Python is installed on your Mac
2. Create a free Reddit account and register a developer app to get API credentials
3. Add Reddit credentials and Anthropic API key to a `.env` file
4. Install dependencies with one Terminal command
5. Launch the app with one Terminal command — after that, it opens in your browser

"""URL scraper: fetches a web page and extracts candidate passages via Claude API."""

# PRAW REDDIT API — activate when developer credentials approved
#
# from contextlib import contextmanager
# from urllib.parse import urlparse as _urlparse
# import re as _re
# import os as _os
#
# import praw
# from prawcore import exceptions as prawcore_exceptions
#
#
# class RedditCredentialsError(Exception):
#     pass
#
#
# class SubredditAccessError(Exception):
#     pass
#
#
# class RedditRateLimitError(Exception):
#     pass
#
#
# _REQUIRED_REDDIT_ENV_VARS = (
#     "REDDIT_CLIENT_ID",
#     "REDDIT_CLIENT_SECRET",
#     "REDDIT_USER_AGENT",
# )
#
#
# @contextmanager
# def _prawcore_error_guard():
#     """Translates prawcore network/auth exceptions into domain errors."""
#     try:
#         yield
#     except (prawcore_exceptions.ResponseException, prawcore_exceptions.OAuthException):
#         raise RedditCredentialsError from None
#     except (
#         prawcore_exceptions.Forbidden,
#         prawcore_exceptions.NotFound,
#         prawcore_exceptions.Redirect,
#     ):
#         raise SubredditAccessError from None
#     except prawcore_exceptions.TooManyRequests:
#         raise RedditRateLimitError from None
#
#
# def _parse_subreddit_name(subreddit_url: str) -> str:
#     raw_value = subreddit_url.strip()
#     if not raw_value:
#         raise ValueError("Please enter a subreddit URL.")
#     if _re.fullmatch(r"[A-Za-z0-9_]+", raw_value):
#         return raw_value
#     direct_match = _re.fullmatch(r"/?r/([A-Za-z0-9_]+)/?", raw_value)
#     if direct_match:
#         return direct_match.group(1)
#     url = raw_value if _re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw_value) else f"https://{raw_value}"
#     path_match = _re.search(r"/r/([A-Za-z0-9_]+)", _urlparse(url).path)
#     if path_match:
#         return path_match.group(1)
#     raise ValueError("Please enter a valid subreddit URL.")
#
#
# def _create_reddit_client() -> praw.Reddit:
#     credentials = {name: _os.getenv(name, "").strip() for name in _REQUIRED_REDDIT_ENV_VARS}
#     if not all(credentials.values()):
#         raise RedditCredentialsError from None
#     return praw.Reddit(
#         client_id=credentials["REDDIT_CLIENT_ID"],
#         client_secret=credentials["REDDIT_CLIENT_SECRET"],
#         user_agent=credentials["REDDIT_USER_AGENT"],
#     )
#
#
# def _build_reddit_record(submission) -> dict:
#     subreddit_name = submission.subreddit.display_name
#     return {
#         "record_id": f"reddit_{submission.id}",
#         "source_type": "reddit",
#         "source_id": f"r/{subreddit_name}",
#         "title": submission.title,
#         "text": submission.selftext,
#         "date_retrieved": date.today().isoformat(),
#         "url": submission.url,
#         "page_ref": "",
#         "search_terms_used": "",
#         "stage_1": "",
#         "stage_2": "",
#         "stage_3": "",
#         "overall_verdict": "",
#         "notes": "",
#     }
#
#
# def scrape_subreddit(subreddit_url: str, min_length: int) -> list:
#     subreddit_name = _parse_subreddit_name(subreddit_url)
#     reddit = _create_reddit_client()
#     with _prawcore_error_guard():
#         subreddit = reddit.subreddit(subreddit_name)
#         _ = subreddit.display_name
#     records = []
#     seen_submission_ids: set[str] = set()
#     with _prawcore_error_guard():
#         for submission in subreddit.new(limit=500):
#             if submission.id in seen_submission_ids:
#                 continue
#             if not submission.selftext:
#                 continue
#             text = submission.selftext.strip()
#             if text in {"[removed]", "[deleted]"}:
#                 continue
#             if len(text) < min_length:
#                 continue
#             seen_submission_ids.add(submission.id)
#             records.append(_build_reddit_record(submission))
#     return records

from datetime import date
import hashlib
import os
from pathlib import Path
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic

from modules.pdf_processor import (
    PDFExtractionError,
    _extract_response_text,
    _parse_claude_json,
    _strip_markdown_fences,
)


class ScraperError(Exception):
    pass


_CHUNK_SIZE = 15000
_CHUNK_OVERLAP = 3000
_NEAR_DUPLICATE_PREFIX_LEN = 200
_EXTRACTION_MODEL = "claude-sonnet-4-6"
_SYSTEM_PROMPT = "You are a precise research assistant. Follow instructions exactly."
_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "pdf_extraction_prompt.txt"


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8").strip()


def _chunk_text(text: str) -> list[str]:
    if len(text) <= _CHUNK_SIZE:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + _CHUNK_SIZE
        if end >= len(text):
            chunks.append(text[start:])
            break
        for sep in ("\n\n", "\n"):
            boundary = text.rfind(sep, start, end)
            if boundary > start:
                end = boundary
                break
        chunks.append(text[start:end])
        start = end - _CHUNK_OVERLAP

    return chunks


def _call_claude(client: Anthropic, prompt: str, content: str) -> list[dict]:
    try:
        response = client.messages.create(
            model=_EXTRACTION_MODEL,
            max_tokens=4000,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"{prompt}\n\n{content}"}],
        )
    except Exception as error:
        raise ScraperError(f"Anthropic API call failed: {str(error)}") from None

    response_text = _strip_markdown_fences(_extract_response_text(response))
    try:
        return _parse_claude_json(response_text)
    except PDFExtractionError as error:
        raise ScraperError(str(error)) from None


def _build_url_record(url: str, domain: str, passage: str, location_hint: str) -> dict:
    normalized = passage.strip()
    return {
        "record_id": f"url_{hashlib.md5(normalized[:100].encode('utf-8')).hexdigest()}",
        "source_type": "url",
        "source_id": domain,
        "title": url,
        "text": normalized,
        "date_retrieved": date.today().isoformat(),
        "url": url,
        "page_ref": location_hint.strip(),
        "search_terms_used": "",
        "stage_1": "",
        "stage_2": "",
        "stage_3": "",
        "overall_verdict": "",
        "notes": "",
    }


def _is_reddit_url(url: str) -> bool:
    return "reddit.com" in url


def _scrape_reddit_json(url: str, min_length: int) -> list:
    json_url = url.rstrip("/") + ".json"
    headers = {"User-Agent": "epiphany-research-tool/1.0 (research purposes)"}

    try:
        response = requests.get(json_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        raise ScraperError(f"Failed to fetch Reddit JSON: {str(error)}") from None
    except ValueError as error:
        raise ScraperError(f"Reddit returned invalid JSON: {str(error)}") from None

    today = date.today().isoformat()
    records = []

    subreddit_match = re.search(r"/r/([A-Za-z0-9_]+)", urlparse(url).path)
    subreddit_name = subreddit_match.group(1) if subreddit_match else "reddit"

    if isinstance(data, dict):
        # Subreddit listing: {"data": {"children": [...]}}
        try:
            children = data["data"]["children"]
        except (KeyError, TypeError):
            raise ScraperError("Unexpected Reddit JSON structure for subreddit listing.") from None

        for child in children:
            try:
                post = child["data"]
            except (KeyError, TypeError):
                continue

            selftext = str(post.get("selftext", "") or "").strip()
            if selftext in ("", "[removed]", "[deleted]"):
                continue
            if len(selftext) < min_length:
                continue

            post_id = str(post.get("id", ""))
            permalink = post.get("permalink", "")
            records.append({
                "record_id": f"reddit_{post_id}",
                "source_type": "reddit",
                "source_id": subreddit_name,
                "title": str(post.get("title", "") or ""),
                "text": selftext,
                "date_retrieved": today,
                "url": f"https://reddit.com{permalink}" if permalink else url,
                "page_ref": "",
                "search_terms_used": "",
                "stage_1": "",
                "stage_2": "",
                "stage_3": "",
                "overall_verdict": "",
                "notes": "",
            })

    elif isinstance(data, list):
        # Post/thread: [post_listing, comments_listing]
        if len(data) < 1:
            raise ScraperError("Reddit returned an empty response for this thread.")

        try:
            post_data = data[0]["data"]["children"][0]["data"]
        except (KeyError, IndexError, TypeError):
            raise ScraperError("Unexpected Reddit JSON structure for post data.") from None

        selftext = str(post_data.get("selftext", "") or "").strip()
        if selftext not in ("", "[removed]", "[deleted]") and len(selftext) >= min_length:
            post_id = str(post_data.get("id", ""))
            permalink = post_data.get("permalink", "")
            records.append({
                "record_id": f"reddit_{post_id}",
                "source_type": "reddit",
                "source_id": subreddit_name,
                "title": str(post_data.get("title", "") or ""),
                "text": selftext,
                "date_retrieved": today,
                "url": f"https://reddit.com{permalink}" if permalink else url,
                "page_ref": "",
                "search_terms_used": "",
                "stage_1": "",
                "stage_2": "",
                "stage_3": "",
                "overall_verdict": "",
                "notes": "",
            })

        if len(data) >= 2:
            try:
                comment_children = data[1]["data"]["children"]
            except (KeyError, TypeError):
                comment_children = []

            for child in comment_children:
                try:
                    comment = child["data"]
                except (KeyError, TypeError):
                    continue

                body = str(comment.get("body", "") or "").strip()
                if body in ("", "[removed]", "[deleted]"):
                    continue
                if len(body) < min_length:
                    continue

                comment_id = str(comment.get("id", ""))
                permalink = comment.get("permalink", "")
                records.append({
                    "record_id": f"reddit_comment_{comment_id}",
                    "source_type": "reddit",
                    "source_id": subreddit_name,
                    "title": "",
                    "text": body,
                    "date_retrieved": today,
                    "url": f"https://reddit.com{permalink}" if permalink else url,
                    "page_ref": "",
                    "search_terms_used": "",
                    "stage_1": "",
                    "stage_2": "",
                    "stage_3": "",
                    "overall_verdict": "",
                    "notes": "",
                })

    else:
        raise ScraperError("Reddit returned an unexpected JSON structure.")

    # Near-duplicate deduplication: keep longest version of passages sharing the same opening
    records.sort(key=lambda r: len(r["text"]), reverse=True)
    seen_prefixes: set[str] = set()
    deduped: list[dict] = []
    for record in records:
        prefix = record["text"][:_NEAR_DUPLICATE_PREFIX_LEN]
        if prefix in seen_prefixes:
            continue
        seen_prefixes.add(prefix)
        deduped.append(record)

    return deduped


def scrape_url(url: str, min_length: int) -> list:
    url = url.strip()
    if not url:
        raise ScraperError("Please enter a URL.")

    if _is_reddit_url(url):
        return _scrape_reddit_json(url, min_length)

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise ScraperError(
            "Anthropic API key not configured. Add ANTHROPIC_API_KEY to your .env file."
        )

    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except requests.RequestException as error:
        raise ScraperError(f"Failed to fetch URL: {str(error)}") from None

    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = [p.get_text(separator=" ", strip=True) for p in soup.find_all("p")]
    page_text = "\n\n".join(p for p in paragraphs if p)

    if len(page_text) < min_length:
        raise ScraperError(
            "Page contains too little text to process. Try a different URL."
        )

    domain = urlparse(url).netloc or url
    prompt = _load_prompt()
    chunks = _chunk_text(page_text)
    client = Anthropic(api_key=api_key)

    records = []
    seen_record_ids: set[str] = set()

    for chunk in chunks:
        raw_passages = _call_claude(client, prompt, chunk)
        for item in raw_passages:
            if not isinstance(item, dict):
                continue
            passage_text = str(item.get("passage", "") or "").strip()
            if not passage_text:
                continue
            location_hint = str(item.get("location_hint", "") or "")
            record = _build_url_record(url, domain, passage_text, location_hint)
            if record["record_id"] in seen_record_ids:
                continue
            seen_record_ids.add(record["record_id"])
            records.append(record)

    # Near-duplicate deduplication: keep the longest version of passages sharing the same opening
    records.sort(key=lambda r: len(r["text"]), reverse=True)
    seen_prefixes: set[str] = set()
    deduped: list[dict] = []
    for record in records:
        prefix = record["text"][:_NEAR_DUPLICATE_PREFIX_LEN]
        if prefix in seen_prefixes:
            continue
        seen_prefixes.add(prefix)
        deduped.append(record)

    return deduped

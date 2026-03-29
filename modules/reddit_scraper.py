"""Scrapes Reddit posts matching search criteria from a given subreddit."""

from datetime import date
import os
import re
from urllib.parse import urlparse

import praw
from prawcore import exceptions as prawcore_exceptions


class RedditCredentialsError(Exception):
    pass


class SubredditAccessError(Exception):
    pass


class RedditRateLimitError(Exception):
    pass


REQUIRED_ENV_VARS = (
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "REDDIT_USER_AGENT",
)


def _parse_subreddit_name(subreddit_url: str) -> str:
    raw_value = subreddit_url.strip()
    if not raw_value:
        raise ValueError("Please enter a subreddit URL.")

    if re.fullmatch(r"[A-Za-z0-9_]+", raw_value):
        return raw_value

    direct_match = re.fullmatch(r"/?r/([A-Za-z0-9_]+)/?", raw_value)
    if direct_match:
        return direct_match.group(1)

    normalized_value = raw_value
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", normalized_value):
        normalized_value = f"https://{normalized_value}"

    parsed = urlparse(normalized_value)
    path_match = re.search(r"/r/([A-Za-z0-9_]+)", parsed.path)
    if path_match:
        return path_match.group(1)

    raise ValueError("Please enter a valid subreddit URL.")


def _create_reddit_client() -> praw.Reddit:
    credentials = {name: os.getenv(name, "").strip() for name in REQUIRED_ENV_VARS}
    if not all(credentials.values()):
        raise RedditCredentialsError

    return praw.Reddit(
        client_id=credentials["REDDIT_CLIENT_ID"],
        client_secret=credentials["REDDIT_CLIENT_SECRET"],
        user_agent=credentials["REDDIT_USER_AGENT"],
    )


def _build_record(submission, search_terms: list[str]) -> dict:
    subreddit_name = submission.subreddit.display_name
    return {
        "record_id": f"reddit_{submission.id}",
        "source_type": "reddit",
        "source_id": f"r/{subreddit_name}",
        "title": submission.title,
        "text": submission.selftext,
        "date_retrieved": date.today().isoformat(),
        "url": submission.url,
        "page_ref": "",
        "search_terms_used": ",".join(search_terms),
        "stage_1": "",
        "stage_2": "",
        "stage_3": "",
        "overall_verdict": "",
        "notes": "",
    }


def scrape_subreddit(subreddit_url: str, search_terms: list, min_length: int) -> list:
    subreddit_name = _parse_subreddit_name(subreddit_url)
    reddit = _create_reddit_client()

    try:
        subreddit = reddit.subreddit(subreddit_name)
        _ = subreddit.display_name
    except (prawcore_exceptions.ResponseException, prawcore_exceptions.OAuthException):
        raise RedditCredentialsError from None
    except (
        prawcore_exceptions.Forbidden,
        prawcore_exceptions.NotFound,
        prawcore_exceptions.Redirect,
    ):
        raise SubredditAccessError from None
    except prawcore_exceptions.TooManyRequests:
        raise RedditRateLimitError from None

    records = []
    seen_submission_ids = set()

    try:
        for search_term in search_terms:
            for submission in subreddit.search(search_term, limit=100):
                if submission.id in seen_submission_ids:
                    continue
                if not submission.selftext:
                    continue

                text = submission.selftext.strip()
                if text in {"[removed]", "[deleted]"}:
                    continue
                if len(text) < min_length:
                    continue

                seen_submission_ids.add(submission.id)
                records.append(_build_record(submission, search_terms))
    except (prawcore_exceptions.ResponseException, prawcore_exceptions.OAuthException):
        raise RedditCredentialsError from None
    except (
        prawcore_exceptions.Forbidden,
        prawcore_exceptions.NotFound,
        prawcore_exceptions.Redirect,
    ):
        raise SubredditAccessError from None
    except prawcore_exceptions.TooManyRequests:
        raise RedditRateLimitError from None

    return records

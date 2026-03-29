from pathlib import Path
import json
import os

import streamlit as st
from dotenv import load_dotenv

from modules.deduplicator import filter_new, mark_seen
from modules.exporter import export_records
from modules.reddit_scraper import (
    RedditCredentialsError,
    RedditRateLimitError,
    SubredditAccessError,
    scrape_subreddit,
)


REQUIRED_ENV_VARS = [
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "REDDIT_USER_AGENT",
    "ANTHROPIC_API_KEY",
]
SEEN_IDS_PATH = Path("output/seen_ids.json")


def ensure_output_directory() -> Path:
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def load_environment() -> tuple[bool, list[str]]:
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)

    missing_vars = [
        variable_name
        for variable_name in REQUIRED_ENV_VARS
        if not os.getenv(variable_name, "").strip()
    ]
    return env_file.exists(), missing_vars


def render_environment_status(env_file_exists: bool, missing_vars: list[str]) -> None:
    st.sidebar.header("Environment Status")

    if env_file_exists and not missing_vars:
        st.sidebar.success("Environment: Ready")
        return

    if not env_file_exists:
        for variable_name in REQUIRED_ENV_VARS:
            st.sidebar.error(f"Missing: {variable_name}")
        return

    for variable_name in missing_vars:
        st.sidebar.error(f"Missing: {variable_name}")


def initialize_session_state() -> None:
    st.session_state.setdefault("records", [])
    st.session_state.setdefault("duplicate_count", 0)
    st.session_state.setdefault("total_records_in_bank", 0)
    st.session_state.setdefault("scrape_attempted", False)


def parse_search_terms(raw_search_terms: str) -> list[str]:
    return [term.strip() for term in raw_search_terms.split(",") if term.strip()]


def load_seen_count() -> int:
    if not SEEN_IDS_PATH.exists():
        return 0

    try:
        with SEEN_IDS_PATH.open("r", encoding="utf-8") as seen_file:
            seen_ids = json.load(seen_file)
    except json.JSONDecodeError:
        return 0

    if not isinstance(seen_ids, list):
        return 0

    return len([record_id for record_id in seen_ids if isinstance(record_id, str)])


def render_results() -> None:
    st.subheader("Results")

    records = st.session_state.get("records", [])
    duplicate_count = st.session_state.get("duplicate_count", 0)
    total_records_in_bank = st.session_state.get("total_records_in_bank", load_seen_count())
    scrape_attempted = st.session_state.get("scrape_attempted", False)

    if not records:
        if scrape_attempted:
            st.info("No posts found matching your search terms.")
            st.write(f"0 new records retrieved. {total_records_in_bank} total records in bank.")
            if duplicate_count > 0:
                st.write(f"{duplicate_count} duplicates skipped.")
        else:
            st.info("No results yet. Run a scrape or upload a PDF to get started.")
    else:
        preview_rows = []
        for record in records:
            preview_rows.append(
                {
                    "source_id": record["source_id"],
                    "title": record["title"],
                    "text preview": record["text"][:200],
                    "date_retrieved": record["date_retrieved"],
                    "url": record["url"],
                }
            )

        st.dataframe(preview_rows, use_container_width=True)
        st.write(f"{len(records)} new records retrieved. {total_records_in_bank} total records in bank.")
        if duplicate_count > 0:
            st.write(f"{duplicate_count} duplicates skipped.")

    export_csv_column, export_json_column = st.columns(2)
    has_records = bool(records)

    with export_csv_column:
        export_csv_clicked = st.button("Export CSV", disabled=not has_records)
    with export_json_column:
        export_json_clicked = st.button("Export JSON", disabled=not has_records)

    if export_csv_clicked or export_json_clicked:
        try:
            exported_count = export_records(records)
            mark_seen(records)
            st.session_state["records"] = []
            st.session_state["total_records_in_bank"] = load_seen_count()
            st.success(f"{exported_count} records exported successfully.")
            st.rerun()
        except Exception as error:
            st.error(f"Unexpected error: {str(error)}")


def main() -> None:
    ensure_output_directory()
    env_file_exists, missing_vars = load_environment()
    st.set_page_config(page_title="Epiphany Narrative Example Bank", layout="wide")
    initialize_session_state()

    render_environment_status(env_file_exists, missing_vars)

    st.title("Epiphany Narrative Example Bank")
    st.write("Retrieve and export candidate epiphanic accounts for manual coding")

    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader("Reddit Scraper")
        subreddit_url = st.text_input(
            "Subreddit URL",
            placeholder="https://www.reddit.com/r/offmychest",
        )
        raw_search_terms = st.text_input(
            "Search Terms (comma-separated)",
            value="I realized, it hit me, that moment, everything changed, it clicked",
        )
        min_length = st.number_input(
            "Minimum Post Length (characters)",
            min_value=100,
            value=500,
        )
        run_reddit_scrape = st.button("Run Reddit Scrape")

    with right_column:
        st.subheader("PDF Processor")
        st.file_uploader("Drop a PDF here", type=["pdf"])
        st.button("Run PDF Extraction", disabled=True)

    if run_reddit_scrape:
        search_terms = parse_search_terms(raw_search_terms)

        try:
            with st.spinner("Retrieving posts from Reddit..."):
                scraped_records = scrape_subreddit(subreddit_url, search_terms, int(min_length))
                new_records = filter_new(scraped_records)

            duplicate_count = len(scraped_records) - len(new_records)
            st.session_state["records"] = new_records
            st.session_state["duplicate_count"] = duplicate_count
            st.session_state["total_records_in_bank"] = load_seen_count() + len(new_records)
            st.session_state["scrape_attempted"] = True
        except ValueError as error:
            st.session_state["records"] = []
            st.session_state["duplicate_count"] = 0
            st.session_state["total_records_in_bank"] = load_seen_count()
            st.session_state["scrape_attempted"] = False
            st.error(str(error))
        except RedditCredentialsError:
            st.session_state["records"] = []
            st.session_state["duplicate_count"] = 0
            st.session_state["total_records_in_bank"] = load_seen_count()
            st.session_state["scrape_attempted"] = False
            st.error(
                "Reddit credentials not configured. Please complete setup in your .env file — see REDDIT_API_SETUP.md."
            )
        except SubredditAccessError:
            st.session_state["records"] = []
            st.session_state["duplicate_count"] = 0
            st.session_state["total_records_in_bank"] = load_seen_count()
            st.session_state["scrape_attempted"] = False
            st.error("Subreddit not found or is private. Check the URL and try again.")
        except RedditRateLimitError:
            st.session_state["records"] = []
            st.session_state["duplicate_count"] = 0
            st.session_state["total_records_in_bank"] = load_seen_count()
            st.session_state["scrape_attempted"] = False
            st.error("Reddit rate limit reached. Please wait 60 seconds and try again.")
        except Exception as error:
            st.session_state["records"] = []
            st.session_state["duplicate_count"] = 0
            st.session_state["total_records_in_bank"] = load_seen_count()
            st.session_state["scrape_attempted"] = False
            st.error(f"Unexpected error: {str(error)}")

    render_results()


if __name__ == "__main__":
    main()

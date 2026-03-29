from pathlib import Path
import os

import streamlit as st
from dotenv import load_dotenv


REQUIRED_ENV_VARS = [
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "REDDIT_USER_AGENT",
    "ANTHROPIC_API_KEY",
]


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

    if missing_vars:
        for variable_name in missing_vars:
            st.sidebar.error(f"Missing: {variable_name}")
        return

    if not env_file_exists:
        for variable_name in REQUIRED_ENV_VARS:
            st.sidebar.error(f"Missing: {variable_name}")


def main() -> None:
    ensure_output_directory()
    env_file_exists, missing_vars = load_environment()

    st.set_page_config(page_title="Epiphany Narrative Example Bank", layout="wide")

    render_environment_status(env_file_exists, missing_vars)

    st.title("Epiphany Narrative Example Bank")
    st.write("Retrieve and export candidate epiphanic accounts for manual coding")

    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader("Reddit Scraper")
        st.text_input(
            "Subreddit URL",
            placeholder="https://www.reddit.com/r/offmychest",
        )
        st.text_input(
            "Search Terms (comma-separated)",
            value="I realized, it hit me, that moment, everything changed, it clicked",
        )
        st.number_input(
            "Minimum Post Length (characters)",
            min_value=100,
            value=500,
        )
        st.button("Run Reddit Scrape", disabled=True)

    with right_column:
        st.subheader("PDF Processor")
        st.file_uploader("Drop a PDF here", type=["pdf"])
        st.button("Run PDF Extraction", disabled=True)

    st.subheader("Results")
    st.info("No results yet. Run a scrape or upload a PDF to get started.")

    export_csv_column, export_json_column = st.columns(2)
    with export_csv_column:
        st.button("Export CSV", disabled=True)
    with export_json_column:
        st.button("Export JSON", disabled=True)


if __name__ == "__main__":
    main()

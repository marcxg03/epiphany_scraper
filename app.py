import csv
from datetime import date
import io
import json
from pathlib import Path
import os
import re
import tempfile
from urllib.parse import urlparse

import streamlit as st
from dotenv import load_dotenv

from modules.deduplicator import filter_new, load_seen_ids, mark_seen
from modules.exporter import export_records, RECORD_FIELDS
from modules.pdf_processor import PDFExtractionError, process_pdf
from modules.reddit_scraper import ScraperError, scrape_url


REQUIRED_ENV_VARS = [
    "ANTHROPIC_API_KEY",
]


def _derive_source_name(records: list) -> str:
    """Return a filesystem-safe name derived from the first record's source."""
    if not records:
        return "export"
    record = records[0]
    source_id = str(record.get("source_id", "") or "export")
    source_type = record.get("source_type", "")
    source_name = Path(source_id).stem if source_type == "pdf" else source_id
    clean = re.sub(r"[^A-Za-z0-9]+", "_", source_name).strip("_")
    return clean or "export"


def _build_csv_content(records: list) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=RECORD_FIELDS)
    writer.writeheader()
    for record in records:
        writer.writerow({field: record.get(field, "") for field in RECORD_FIELDS})
    return buf.getvalue()


def _build_json_content(records: list) -> str:
    normalized = [{field: record.get(field, "") for field in RECORD_FIELDS} for record in records]
    return json.dumps(normalized, indent=2)


def ensure_output_directory() -> Path:
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def load_environment() -> tuple[bool, list[str]]:
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)

    missing_vars = [
        var for var in REQUIRED_ENV_VARS
        if not os.getenv(var, "").strip()
    ]
    return env_file.exists(), missing_vars


def render_environment_status(env_file_exists: bool, missing_vars: list[str]) -> None:
    st.sidebar.header("Environment Status")

    if env_file_exists and not missing_vars:
        st.sidebar.success("Environment: Ready")
        return

    if not env_file_exists:
        for var in REQUIRED_ENV_VARS:
            st.sidebar.error(f"Missing: {var}")
        return

    for var in missing_vars:
        st.sidebar.error(f"Missing: {var}")


def load_seen_count() -> int:
    return len(load_seen_ids())


def initialize_session_state() -> None:
    st.session_state.setdefault("records", [])
    st.session_state.setdefault("duplicate_count", 0)
    st.session_state.setdefault("total_records_in_bank", load_seen_count())
    st.session_state.setdefault("run_attempted", False)
    st.session_state.setdefault("empty_results_message", "No posts found matching your search terms.")
    st.session_state.setdefault("session_history", [])
    st.session_state.setdefault("session_cleared_message", False)


def _reset_run_state() -> None:
    """Resets results session state after a failed run."""
    st.session_state["records"] = []
    st.session_state["duplicate_count"] = 0
    st.session_state["total_records_in_bank"] = load_seen_count()
    st.session_state["run_attempted"] = False


def render_sidebar_controls() -> None:
    if st.session_state.get("records"):
        if st.sidebar.button("Clear Session"):
            st.session_state["records"] = []
            st.session_state["duplicate_count"] = 0
            st.session_state["session_history"] = []
            st.session_state["run_attempted"] = False
            st.session_state["empty_results_message"] = "No posts found matching your search terms."
            st.session_state["session_cleared_message"] = True
            st.sidebar.success("Session cleared.")
            st.rerun()

    if st.session_state.get("session_cleared_message"):
        st.sidebar.success("Session cleared.")
        st.session_state["session_cleared_message"] = False

    if st.session_state.get("session_history"):
        st.sidebar.subheader("This Session")
        for item in st.session_state["session_history"]:
            st.sidebar.caption(item)


def render_bank_viewer() -> None:
    bank_path = Path("output") / "example_bank.json"

    st.sidebar.markdown("---")
    st.sidebar.subheader("Example Bank")

    all_records: list = []
    if bank_path.exists():
        try:
            with bank_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = []
            all_records = data
        except json.JSONDecodeError:
            st.sidebar.warning("Bank file could not be read.")
            return
        except OSError:
            return

    if not all_records:
        st.sidebar.caption("Bank is empty.")
        return

    st.sidebar.caption(f"{len(all_records)} total records")

    selected_type = st.sidebar.radio("Browse by", options=["reddit", "pdf", "url"], horizontal=True)

    type_records = [r for r in all_records if r.get("source_type", "") == selected_type]
    unique_sources = sorted({r.get("source_id", "") for r in type_records if r.get("source_id")})

    if not unique_sources:
        st.sidebar.caption(f"No {selected_type} records in bank.")
        return

    selected_source = st.sidebar.selectbox("Source", options=unique_sources)

    source_records = [r for r in type_records if r.get("source_id", "") == selected_source]
    st.sidebar.caption(f"{len(source_records)} records from {selected_source}")

    today = date.today().isoformat()
    safe_source = re.sub(r"[^A-Za-z0-9]+", "_", selected_source).strip("_")
    csv_col, json_col = st.sidebar.columns(2)
    with csv_col:
        st.download_button(
            "Export CSV",
            data=_build_csv_content(source_records),
            file_name=f"{safe_source}_{today}.csv",
            mime="text/csv",
            disabled=not source_records,
            key="bank_export_csv",
        )
    with json_col:
        st.download_button(
            "Export JSON",
            data=_build_json_content(source_records),
            file_name=f"{safe_source}_{today}.json",
            mime="application/json",
            disabled=not source_records,
            key="bank_export_json",
        )


def render_full_text_expanders(records: list[dict]) -> None:
    if not records:
        return

    st.subheader("Full Passage Text")
    for record in records:
        label = f"{record['title'][:60]} — {record['date_retrieved']}"
        with st.expander(label):
            st.write(record["text"])
            st.caption(f"Source: {record['source_id']}")
            if record["url"]:
                st.caption(f"URL: {record['url']}")
            if record["page_ref"]:
                st.caption(f"Page: {record['page_ref']}")


def render_results() -> None:
    st.subheader("Results")

    records = st.session_state.get("records", [])
    duplicate_count = st.session_state.get("duplicate_count", 0)
    total_records_in_bank = st.session_state.get("total_records_in_bank", 0)
    run_attempted = st.session_state.get("run_attempted", False)
    empty_results_message = st.session_state.get(
        "empty_results_message", "No posts found matching your search terms."
    )

    if not records:
        if run_attempted:
            st.info(empty_results_message)
            st.write(f"0 new records retrieved. {total_records_in_bank} total records in bank.")
            if duplicate_count > 0:
                st.write(f"{duplicate_count} duplicates skipped.")
        else:
            st.info("No results yet. Run a scrape or upload a PDF to get started.")
    else:
        preview_rows = [
            {
                "source_id": record["source_id"],
                "title": record["title"],
                "text preview": record["text"][:200],
                "date_retrieved": record["date_retrieved"],
                "url": record["url"],
            }
            for record in records
        ]
        st.dataframe(preview_rows, use_container_width=True)
        st.write(f"{len(records)} new records retrieved. {total_records_in_bank} total records in bank.")
        if duplicate_count > 0:
            st.write(f"{duplicate_count} duplicates skipped.")
        render_full_text_expanders(records)

    has_records = bool(records)

    if has_records:
        source_name = _derive_source_name(records)
        today = date.today().isoformat()
        csv_content = _build_csv_content(records)
        json_content = _build_json_content(records)
        csv_filename = f"{source_name}_{today}.csv"
        json_filename = f"{source_name}_{today}.json"
    else:
        csv_content = json_content = ""
        csv_filename, json_filename = "export.csv", "export.json"

    csv_col, json_col = st.columns(2)
    with csv_col:
        export_csv_clicked = st.download_button(
            "Export CSV",
            data=csv_content,
            file_name=csv_filename,
            mime="text/csv",
            disabled=not has_records,
        )
    with json_col:
        export_json_clicked = st.download_button(
            "Export JSON",
            data=json_content,
            file_name=json_filename,
            mime="application/json",
            disabled=not has_records,
        )

    if export_csv_clicked or export_json_clicked:
        try:
            exported_count = export_records(records)
            mark_seen(records)
            st.session_state["records"] = []
            st.session_state["duplicate_count"] = 0
            st.session_state["run_attempted"] = False
            st.session_state["empty_results_message"] = "No posts found matching your search terms."
            st.session_state["total_records_in_bank"] = load_seen_count()
            st.success(f"{exported_count} records exported successfully.")
        except Exception as error:
            st.error(f"Unexpected error: {str(error)}")


def main() -> None:
    ensure_output_directory()
    env_file_exists, missing_vars = load_environment()
    st.set_page_config(page_title="Epiphany Narrative Example Bank", layout="wide")
    initialize_session_state()

    render_environment_status(env_file_exists, missing_vars)
    render_sidebar_controls()
    render_bank_viewer()

    st.title("Epiphany Narrative Example Bank")
    st.write("Retrieve and export candidate epiphanic accounts for manual coding")

    reddit_col, pdf_col = st.columns(2)

    with reddit_col:
        st.subheader("URL Scraper")
        page_url = st.text_input(
            "Page URL",
            placeholder="https://www.reddit.com/r/offmychest",
        )
        min_length = st.number_input(
            "Minimum Text Length (characters)",
            min_value=100,
            value=500,
        )
        run_url_scrape = st.button("Run URL Scrape")

    with pdf_col:
        st.subheader("PDF Processor")
        uploaded_pdf = st.file_uploader("Drop a PDF here", type=["pdf"])
        run_pdf_extraction = st.button(
            "Run PDF Extraction",
            disabled=uploaded_pdf is None,
        )

    if run_url_scrape:
        try:
            with st.spinner("Fetching page and extracting passages..."):
                scraped_records = scrape_url(page_url, min_length)
                new_records = filter_new(scraped_records)
            domain = urlparse(page_url.strip()).netloc or page_url.strip()
            st.session_state["records"] = new_records
            st.session_state["duplicate_count"] = len(scraped_records) - len(new_records)
            st.session_state["total_records_in_bank"] = load_seen_count() + len(new_records)
            st.session_state["run_attempted"] = True
            st.session_state["empty_results_message"] = "No candidate passages found at this URL."
            st.session_state["session_history"].append(f"{domain} — {len(new_records)} records")
            st.rerun()
        except ScraperError as error:
            _reset_run_state()
            st.error(str(error))
        except Exception as error:
            _reset_run_state()
            st.error(f"Unexpected error: {str(error)}")

    if run_pdf_extraction and uploaded_pdf is not None:
        temp_path = None
        try:
            file_suffix = Path(uploaded_pdf.name).suffix or ".pdf"
            safe_stem = "".join(
                c if c.isalnum() else "_"
                for c in (Path(uploaded_pdf.name).stem or "uploaded_pdf")
            )
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=file_suffix, prefix=f"{safe_stem}_"
            ) as tmp:
                tmp.write(uploaded_pdf.getvalue())
                temp_path = tmp.name

            with st.spinner("Extracting passages from PDF..."):
                extracted_records = process_pdf(temp_path)
                for record in extracted_records:
                    record["source_id"] = uploaded_pdf.name
                    record["title"] = uploaded_pdf.name
                new_records = filter_new(extracted_records)

            st.session_state["records"] = new_records
            st.session_state["duplicate_count"] = len(extracted_records) - len(new_records)
            st.session_state["total_records_in_bank"] = load_seen_count() + len(new_records)
            st.session_state["run_attempted"] = True
            st.session_state["empty_results_message"] = "No candidate passages found in this PDF."
            st.session_state["session_history"].append(
                f"{uploaded_pdf.name} — {len(new_records)} records"
            )
            st.rerun()
        except PDFExtractionError as error:
            _reset_run_state()
            st.error(str(error))
        except Exception as error:
            _reset_run_state()
            st.error(f"Unexpected error: {str(error)}")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    render_results()


if __name__ == "__main__":
    main()

# Epiphany Narrative Example Bank Retrieval Tool

A local research tool that retrieves candidate epiphanic accounts and exports them for manual coding.

## Requirements

- Python 3.11+

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with:

```env
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=
ANTHROPIC_API_KEY=
```

## Run

```bash
streamlit run app.py
```

The app will create the `output/` directory automatically if it does not already exist.

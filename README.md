# Agno Video AI Summarizer — README

A compact Streamlit app that uses the **Agno** agent + Google Gemini (multimodal) to analyze uploaded videos and answer user questions about their content. The app uploads the video temporarily, sends it to the agent for multimodal analysis, and returns a human-readable summary/answer.

---

## Quick demo / TL;DR

1. Create a `.env` file with your Google API key:
   `GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"`
2. Install dependencies: `pip install -r requirements.txt`
3. Run app:
   `streamlit run app.py`
4. Open the Streamlit UI in your browser, upload an MP4/MOV/AVI, type a question, click **Analyze Video**.

---

## What’s included

* `app.py` — Streamlit frontend & Agno agent logic. Uploads a video, creates a temporary file, sends it to the Agno `Agent` (Gemini model) and shows the AI response.
* `requirements.txt` — Python dependencies needed to run the app.

Supported video input types: `.mp4`, `.mov`, `.avi`.

---

## Installation

1. (Recommended) Create and activate a virtual environment:

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

2. Install packages:

```bash
pip install -r requirements.txt
```

---

## Configuration / API Key

The app requires a Google API key set in an environment variable named `GOOGLE_API_KEY`. The app reads this with `python-dotenv` from a local `.env` file.

Create a `.env` file (same folder as `app.py`) with:

```
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
```

### How to generate a Google API Key (high-level steps)

> The exact UI/labels on Google Cloud can change — these are the standard steps you should follow:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Ensure **Billing** is enabled for the project (GenAI calls require billing).
4. Enable the **Generative AI API** (or relevant GenAI / Gemini API) for your project.
5. Create credentials:

   * For a simple API-key-based approach: Go to **APIs & Services → Credentials → Create credentials → API key**.
   * (Optional/Recommended) For production or tighter security, create a **Service Account** and use service account credentials / OAuth where supported.
6. (Strongly recommended) Restrict the API key to the specific APIs, set HTTP referrers or IP restrictions, and rotate keys periodically.
7. Copy the API key and place it into your `.env` as `GOOGLE_API_KEY`.

**Common problems**

* `403 PERMISSION_DENIED` often means the API key lacks permission, the API is not enabled, or billing is not active. Verify your project’s billing and API enablement.
* If you see `contents are required` or the app reports video upload failures, double-check key permissions and billing first.

---

## Usage

Start the app:

```bash
streamlit run app.py
```

App flow:

1. Upload a video file (`mp4`, `mov`, `avi`).
2. Provide a query in the text area (what you want the AI to analyze or extract).
3. Click **Analyze Video**.
4. App shows a spinner while the agent runs, then prints the AI response (markdown). Temporary files are removed automatically.

Notes:

* The app generates a short unique ID for each uploaded file and stores it in a temporary file on disk while processing.
* The agent may perform supplemental web research (DuckDuckGoTools present in the setup).

---

## Security & best practices

* **Never** commit `.env` or keys to source control. Add `.env` to `.gitignore`.
* Restrict your API key in Google Cloud (by API & by referrer/IP) whenever possible.
* Rotate keys regularly and limit permissions to the minimum required.
* Monitor billing and set notifications/quotas to avoid unexpected charges.

---

## Troubleshooting

* **No API key found** — The app will show an error and stop. Ensure `GOOGLE_API_KEY` is present in `.env` or environment.
* **403 / PERMISSION_DENIED** — Check that the GenAI API (or relevant API) is enabled and billing is active for the project; check key restrictions and permissions.
* **Video upload fails** — Try a smaller video; check disk space and that the temp file was created. The app will attempt to clean up temp files automatically.
* **Model / API errors** — Inspect the Streamlit logs printed to console for stack traces; check API key scope, quota, and billing.

---

## Development & contributions

* The app is intentionally minimal and intended as an example integration of Agno + Gemini for multimodal video analysis.
* To extend: add more file-format handling, progress feedback, more agent prompt controls, or richer output formats (SRT, timestamps, etc.).

---

## License & disclaimers

* This is a sample/demo app. Use responsibly and ensure compliance with Google Cloud terms and any data privacy laws relevant to your content.
* Keep API keys and sensitive data secure.

---

## 👤 Author
Mansoor Khan    
GitHub: [rebase-master](https://github.com/rebase-master)


# Analytics AutoPilot — Master Blueprint & Mentor Rules

## 1. AI Co-Founder & Mentor Persona
You are my **Senior Technical Co-Founder, Lead Data Engineer, and SaaS Product Advisor**.
- **My Profile:** Engineering background + Data Analytics trainee (Python, SQL, Excel, PowerBI) with HTML, CSS, JS, and basic React skills. My ultimate goal is to build a profitable, real-world SaaS business.
- **How I Learn Best:** I am still building confidence in full-stack software architecture, backend systems, and security. Do **not** leave me "at your mercy" blindly accepting huge code rewrites I don't understand.
- **Communication Rules:**
  1. **Protect Working Code:** Keep our "Linear Obsidian" UI in `app.py`, our modular engines (`analysis_engine.py`, `chart_engine.py`, `slide_builder.py`), and our interactive 16:9 slide carousel. Improve incrementally without breaking working features.
  2. **One Step at a Time:** Never dump 500 lines of code or 10 tasks at once. Pick the **single next unchecked task** below and walk me through it until tested and working.
  3. **Explain the "Why" Simply:** Briefly explain what each change does and why we are doing it in plain English so I understand every line of my codebase and can defend it in interviews.
  4. **Proactively Spot Risks & Audit Yourself:** Always think critically like a senior engineer—spot edge cases, API key leaks, messy CSV crashes, and multi-user concurrency issues before they happen, and update checkboxes `[x]` in `MASTER_PLAN.md` as we complete them.

## 2. Core Architecture Rules
- **Python is the Backbone:** `analysis_engine.py` (`pandas`) computes 100% of KPIs, trends, and rankings deterministically. `chart_engine.py` (`Plotly` + `kaleido`) renders PNGs, and `slide_builder.py` (`python-pptx`) builds the deck.
- **Single Source of Truth:** `app.py` must delegate data cleaning and KPI math to `analysis_engine.py` rather than duplicating `groupby` logic inside the UI file.
- **AI is the Smart Narrator (Never the Math Engine):**
  - Pass ONLY the verified KPI/summary dictionary from `analysis_engine.py` to the **Gemini API** (`google-genai`) so it generates executive takeaways, strategic recommendations, and speaker notes without ever hallucinating math or exposing raw user rows.

## 3. PHASE 1: Streamlit Beta (CV & Portfolio Ready MVP)
*Goal: A crash-proof, AI-powered live web app for my CV, LinkedIn, and 10–20 beta testers.*

### A. Completed Foundation (v0.1)
- [x] Modular file structure (`analysis_engine.py`, `chart_engine.py`, `slide_builder.py`, `run_pipeline.py`, `generate_data.py`)
- [x] Linear Obsidian Streamlit UI with dynamic chart-type switchers & interactive 16:9 slide preview (`app.py`)

### B. Immediate Bug Fixes & Code Consolidation
- [x] Pass user's custom `report_title` from `app.py` into `build_presentation()` -> `slide_title()` in `slide_builder.py` (currently hardcoded to `"2024 Annual Sales Report"`).
- [x] Refactor `app.py` to call `analysis_engine.py` (`build_report()`) instead of duplicating KPI/groupby calculations inline.
- [ ] Harden `analysis_engine.py` for messy real-world uploads: strip currency symbols (`$`, `GHS`, commas) before numeric conversion, handle missing `Profit`/`Cost` columns gracefully (allow "None / Not Available"), and wrap uploads in friendly `try/except` alerts.
- [ ] Fix `chart_engine.py` PNG export reliability (ensure `kaleido` works cleanly or add a reliable fallback image generator so `slide_builder.py` never receives an `.html` file).

### C. AI Narrative Integration (v0.3)
- [ ] Create `ai_narrator.py` using the Gemini API (`google-genai`) with API keys stored safely in `.env` (local) and `st.secrets` (cloud) — never hardcoded.
- [ ] Feed ONLY the structured KPI/insights JSON from `analysis_engine.py` into Gemini to generate tailored executive takeaways, 4 strategic recommendations, and slide-by-slide speaker notes.
- [ ] Keep our existing deterministic template text as an automatic fallback if the API key is missing or the API call fails.
- [ ] Cache AI responses in `st.session_state` so changing chart styles or clicking slide tabs does NOT re-trigger paid Gemini API calls.

### D. SaaS-Ready Concurrency, Branding & Deployment
- [ ] Replace the shared `output/` directory in `chart_engine.py` and `slide_builder.py` with `tempfile.TemporaryDirectory()` (or session-scoped paths) so simultaneous users never overwrite each other's charts/decks.
- [ ] Add Custom Branding v0.2 (optional company logo upload + primary accent color picker passed into `slide_builder.py`).
- [ ] Deploy live to **Streamlit Community Cloud** and share with 10–15 beta testers for real-world feedback.

## 4. PHASE 2: Commercial SaaS Product (v1.0 Paid Full-Stack)
*Goal: Monetize the validated Python engines into a secure multi-user SaaS.*

- [ ] **Decouple Backend & Frontend:** Wrap `analysis_engine.py`, `chart_engine.py`, `ai_narrator.py`, and `slide_builder.py` inside a **FastAPI** backend; build a **React / Next.js** frontend.
- [ ] **Auth & Database:** Set up **Supabase** (PostgreSQL + Auth + Storage) with user accounts, usage credits, and automatic 1-hour deletion of uploaded datasets.
- [ ] **Security & Rate Limiting:** Validate real file headers on upload, sanitize cells against formula injection, lock down CORS, and rate-limit endpoints to protect Gemini API credits.
- [ ] **Payments & Tiers:** Add Free Tier (2 decks/month, watermarked) vs. Pro Tier ($15–$29/mo or GHS equivalent, unlimited decks, custom brand kit) via **Paystack** (Ghana/Africa cards & Mobile Money) and/or **Stripe / Lemon Squeezy**.

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
  5. **Push Back on Bad or Risky Ideas:** Never be a "yes-man." If I suggest a feature, UI tweak, or refactor that is unnecessary, over-complicated, or risks breaking working functionality, stop and warn me honestly before writing code. Explain the trade-off and propose a cleaner, safer alternative.
  6. **Mandatory Self-Audit After Every Edit:** Whenever you finish modifying code, review your own diff before responding to me—actively check for broken imports, missing variables, messy-CSV edge cases, or unintended side effects across `app.py`, `analysis_engine.py`, `chart_engine.py`, `ai_narrator.py`, and `slide_builder.py`, and tell me what you verified.

## 2. Core Architecture & Product Differentiation Rules
- **Escaping the "ChatGPT Trap" (Opinionated Workflows):** Generic "upload any CSV for generic AI insights" tools lose to ChatGPT. We differentiate through: (1) 100% deterministic math accuracy, (2) executive-ready branded PowerPoint slide design, and (3) selectable **Report Modes** tailored to specific business workflows (Sales & Retail, Marketing Campaign ROI, Operations & Expenses).
- **Python is the Backbone:** `analysis_engine.py` (`pandas`) computes 100% of KPIs, trends, and rankings deterministically. `chart_engine.py` (`Plotly` + `kaleido`) renders PNGs, and `slide_builder.py` (`python-pptx`) builds the deck.
- **Single Source of Truth:** `app.py` must delegate data cleaning and KPI math to `analysis_engine.py` rather than duplicating `groupby` logic inside the UI file.
- **AI is the Smart Narrator (Never the Math Engine):**
  - Pass ONLY the verified KPI/summary dictionary from `analysis_engine.py` (plus the selected Report Mode) to the **Gemini API** (`google-genai`) so it generates role-specific executive takeaways, strategic recommendations, and speaker notes without ever hallucinating math or exposing raw user rows.

## 3. PHASE 1: Streamlit Beta (CV & Portfolio Ready MVP)
*Goal: A crash-proof, AI-powered live web app for my CV, LinkedIn, and 10–20 beta testers.*

### A. Completed Foundation (v0.1)
- [x] Modular file structure (`analysis_engine.py`, `chart_engine.py`, `slide_builder.py`, `run_pipeline.py`, `generate_data.py`)
- [x] Linear Obsidian Streamlit UI with dynamic chart-type switchers & interactive 16:9 slide preview (`app.py`)

### B. Immediate Bug Fixes & Code Consolidation
- [x] Pass user's custom `report_title` from `app.py` into `build_presentation()` -> `slide_title()` in `slide_builder.py`.
- [x] Refactor `app.py` to call `analysis_engine.py` (`build_report()`) instead of duplicating KPI/groupby calculations inline.
- [x] Harden `analysis_engine.py` for messy real-world uploads (currency symbols, missing `Profit`/`Cost` columns, friendly `try/except` alerts).
- [x] Fix `chart_engine.py` PNG export reliability so `slide_builder.py` never receives an `.html` file.

### C. AI Narrative Integration (v0.3)
- [x] Create `ai_narrator.py` using the Gemini API (`google-genai`) with API keys stored safely in `.env` and `st.secrets`.
- [x] Feed ONLY structured KPI/insights JSON from `analysis_engine.py` into Gemini for executive takeaways, strategic recommendations, and speaker notes.
- [x] Keep deterministic template text as automatic fallback and cache AI responses in `st.session_state`.

### D. Niche Differentiation, Trust Polish & Deployment
- [x] Add **"Report Mode" selector** in `app.py` (`Sales & Retail Performance`, `Marketing & Ad Campaign ROI`, `Operations & Expense Tracker`) adapting KPI labels, Gemini prompts, and slide titles.
- [x] **Anomaly & Outlier Flags:** Add a quick Z-score / IQR check in `analysis_engine.py` on time-series metrics so notable spikes or drops are flagged in the summary JSON for Gemini to highlight.
- [x] **Data Health & Cleaning Audit Log:** Record automated cleaning steps in `analysis_engine.py` (e.g., rows cleaned, currency symbols stripped, missing values handled) and display a compact "Data Hygiene" summary in the UI.
- [x] Replace the shared `output/` directory in `chart_engine.py` and `slide_builder.py` with `tempfile.TemporaryDirectory()` (or session-scoped paths) so simultaneous users never overwrite each other's charts/decks.
- [x] Merge `ui-redesign` branch cleanly into `main` once sidebar layout & CSS polish are verified.
- [x] Pre-deployment edge-case hardening (sync chart dropdown state to PPTX, dynamic currency symbols `₵`/`₦`/`£`/`€`/`$`, horizontal bar for >5 products, multi-sheet Excel support, pinned `kaleido==0.2.1`, production reload cleanup).
- [ ] Deploy live to **Streamlit Community Cloud** and share with 10–15 beta testers for real-world feedback.

### E. Pre-Launch Quality & Trust Hardening

#### Milestone 1: Critical Bugs & File Handling (Data Integrity)
- [x] **Fix Stale Data Cache (`app.py`):** Pass a hash of the DataFrame/file bytes as a normal argument to `get_cached_report()` (since `_df` with a leading underscore is ignored by Streamlit's cache), so uploading a second file with identical column names always recomputes fresh metrics.
- [x] **Fix `NameError` Guard (`app.py`):** Define `anomalies = insights.get("anomalies", [])` above `if narrative.get("executive_summary"):` so missing JSON keys never crash the chart header.
- [x] **Harden File Ingestion (`app.py` & `requirements.txt`):** Add `xlrd>=2.0.1` to `requirements.txt` for `.xls` files, and add UTF-8 -> `cp1252`/`latin1` encoding fallback + delimiter sniffing (`sep=None, engine="python"`) for CSVs containing `₵` or `£`.
- [ ] **Harden Number & Date Sanitization (`analysis_engine.py`):** Handle accounting negatives like `(500)` -> `-500`, European decimals (`1.234,56`), and `K`/`M` suffixes safely; flag/report actual imputed/dropped rows honestly in `hygiene` instead of hardcoding `"100% retention"` and `"Certified Clean"` when rows were altered.

#### Milestone 2: True Per-Mode Math & Honest Narratives
- [ ] **True Mode-Specific Metrics (`analysis_engine.py`):** Stop simply relabeling Sales math:
  - *Sales:* Margin % = `Profit / Revenue * 100`, AOV = `Revenue / Orders`
  - *Marketing:* ROAS = `Return / Spend` (or `Conversions / Spend * 100` if return is unmapped), CPA = `Spend / Conversions`
  - *Operations:* Variance = `Actual - Budget`, Budget Utilization % = `Actual / Budget * 100` (with green/amber/red status pills where `<= 100%` is on-budget and `> 100%` is over-budget).
- [ ] **Honest Time-Series & Anomalies (`analysis_engine.py`):** Fix the hardcoded upward arrow (`↑`) when `avg_mom_growth` is negative; ensure "Dominant channel" only shows when a Channel column actually exists; soften anomaly wording so normal 1.5σ fluctuations aren't overclaimed.
- [ ] **Dynamic Currency & Grounded Claims in AI (`ai_narrator.py`):** Pass `currency_symbol` into `generate_narrative()` and `get_deterministic_fallback()` instead of hardcoding `$`, and remove unsupported claims (like "high organic repeat rates" or "ramp up 45 days prior") unless backed by actual data.

#### Milestone 3: PowerPoint Deck & UI Polish
- [ ] **Fix Stretched Charts in `.pptx` (`slide_builder.py`):** Pass ONLY `width` (or ONLY `height`) to `slide.shapes.add_picture()`—or render charts at matching slot aspect ratios—so donuts stay round circles instead of stretched ovals.
- [ ] **Clean Up Slide Layouts (`slide_builder.py`):** Remove the printed "Speaker Notes:" box from the visible face of Slides 3 & 4 (keep speaker scripts strictly in PowerPoint's native Presenter Notes pane across all 5 slides); hide Return Rate / Total Units cards on Slide 2 when those columns aren't mapped; only show the white-label brand header on Slide 1 instead of hardcoding "Analytics AutoPilot" when custom branding is active.
- [ ] **Brand Contrast & Security (`app.py` & `slide_builder.py`):** Add a luminance contrast check so white text on light custom brand colors automatically switches to dark text (`#0F172A`), and wrap user-supplied strings (`report_title`, CSV values, LLM outputs) in `html.escape()` before rendering inside `unsafe_allow_html` blocks.
- [ ] **Protect Server Gemini Key & Add Explicit Trigger (`app.py`):** Add an explicit **"✨ Generate AI Commentary"** button (instead of auto-firing paid API calls on every title/currency tweak) and guard server-side API key usage if no user key is entered.

#### Milestone 4: Shared Architecture & Automated Tests
- [ ] **Centralize Column Inference (`analysis_engine.py`):** Move `infer_mapping()` into `analysis_engine.py` so both `app.py` and `run_pipeline.py` can auto-detect columns on any CSV.
- [ ] **Seasonal Sample Data & Dynamic Year (`generate_data.py` & `app.py`):** Add realistic Q4/holiday seasonality to `generate_sales_data()` so demo insights look authentic, and replace hardcoded `"2024"` titles with the dataset's actual detected year.
- [ ] **Automated Golden Tests (`tests/test_engine.py`):** Add a compact `pytest` suite verifying seeded KPI math, `sanitize_numeric_column` edge cases (`₵1,200.50`, `(500)`, `1.5K`), and Marketing/Operations formulas.

## 4. PHASE 2: Commercial SaaS Product (v1.0 Paid Full-Stack)
*Goal: Monetize the validated Python engines into a secure multi-user SaaS.*

- [ ] **Decouple Backend & Frontend:** Wrap `analysis_engine.py`, `chart_engine.py`, `ai_narrator.py`, and `slide_builder.py` inside a **FastAPI** backend; build a **React / Next.js** frontend.
- [ ] **Auth & Database:** Set up **Supabase** (PostgreSQL + Auth + Storage) with user accounts, usage credits, and automatic 1-hour deletion of uploaded datasets.
- [ ] **Security & Rate Limiting:** Validate real file headers on upload, sanitize cells against formula injection, lock down CORS, and rate-limit endpoints to protect Gemini API credits.
- [ ] **Multi-File Comparison Mode (MoM / Budget vs. Actuals):** Allow uploading two datasets (e.g., Last Month vs. This Month, or Budget vs. Actuals) to compute exact variance metrics and AI variance commentary.
- [ ] **"What-If" Sensitivity Simulator:** Interactive sliders in the frontend (e.g., +5% price, -8% cost) that recalculate projected profit margins in real time and append a "Projected Scenario" slide to the `.pptx`.
- [ ] **Payments & Tiers:** Add Free Tier (2 decks/month, watermarked) vs. Pro Tier ($15–$29/mo or GHS equivalent, unlimited decks, custom brand kit) via **Paystack** (Ghana/Africa cards & Mobile Money) and/or **Stripe / Lemon Squeezy**.

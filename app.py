"""
app.py  —  Analytics AutoPilot
Design System: Linear Obsidian (Dark Pro Studio)
Run with:  python -m streamlit run app.py
"""

import html
import re
import datetime
import streamlit as st
import pandas as pd
import os, io
import plotly.graph_objects as go

def h(val):
    """HTML-escape user and dynamic strings before rendering in unsafe_allow_html blocks."""
    return html.escape(str(val)) if val is not None else ""

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Analytics AutoPilot",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# LINEAR OBSIDIAN DESIGN SYSTEM (CSS)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Global Reset & Base */
html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"], .stApp, .main {
    background-color: #0B0F19 !important;
    background: #0B0F19 !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #F8FAFC !important;
}

[data-testid="stSidebar"] {
    background-color: #111827 !important;
    border-right: 1px solid #1F2937 !important;
}
[data-testid="stSidebarHeader"] {
    padding-top: 0.5rem !important;
    padding-bottom: 0rem !important;
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
    min-height: auto !important;
    height: auto !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 0.25rem !important;
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
    padding-bottom: 3rem !important;
}
[data-testid="stHeader"]  { background: transparent !important; }
.block-container { padding: 1.5rem 3rem 4rem !important; max-width: 1400px; }

/* Navigation Bar */
.ap-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 0 20px;
    border-bottom: 1px solid #1F2937;
    margin-bottom: 28px;
}
.ap-logo-group {
    display: flex;
    align-items: center;
    gap: 12px;
}
.ap-logo-icon {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 800;
    color: #FFFFFF;
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
}
.ap-logo-text {
    font-size: 18px;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #F8FAFC;
}
.ap-logo-text span {
    background: linear-gradient(90deg, #818CF8, #C084FC);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.ap-badge {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 3px 9px;
    border-radius: 20px;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #A5B4FC;
}
.ap-tagline {
    font-size: 13px;
    color: #64748B;
    font-weight: 500;
}

/* Hero Section */
.hero-box {
    background: radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.12) 0%, transparent 70%), #111827;
    border: 1px solid #1F2937;
    border-radius: 16px;
    padding: 32px 36px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.hero-headline {
    font-size: 26px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.02em;
    margin-bottom: 8px;
}
.hero-desc {
    font-size: 14px;
    color: #94A3B8;
    max-width: 680px;
    line-height: 1.6;
}

/* Control Rail */
.control-rail {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 28px;
}

/* KPI Cards */
.kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 28px;
}
.kpi-card {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 14px;
    padding: 22px 24px;
    position: relative;
    overflow: hidden;
    transition: transform 0.15s ease, border-color 0.15s ease;
}
.kpi-card:hover {
    border-color: rgba(99, 102, 241, 0.4);
    transform: translateY(-2px);
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #6366F1, #38BDF8);
}
.kpi-label {
    font-size: 11px;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
}
.kpi-value {
    font-size: 28px;
    font-weight: 800;
    color: #F8FAFC;
    letter-spacing: -0.03em;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.kpi-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-top: 10px;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 20px;
}
.pill-red { background: rgba(239, 68, 68, 0.12); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.25); }
.pill-green { background: rgba(16, 185, 129, 0.12); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.25); }
.pill-purple { background: rgba(139, 92, 246, 0.12); color: #C084FC; border: 1px solid rgba(139, 92, 246, 0.25); }
.pill-blue   { background: rgba(56, 189, 248, 0.12); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.25); }
.pill-amber  { background: rgba(245, 158, 11, 0.12); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.25); }

/* Chart Containers */
.chart-box {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 20px;
}

/* Insight Cards */
.insight-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 28px;
}
.insight-card {
    background: #111827;
    border: 1px solid #1F2937;
    border-left: 3px solid #6366F1;
    border-radius: 12px;
    padding: 20px;
}
.insight-title {
    font-size: 12px;
    font-weight: 700;
    color: #818CF8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.insight-body {
    font-size: 13px;
    color: #94A3B8;
    line-height: 1.6;
}

/* Section Header */
.section-title {
    font-size: 13px;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1F2937;
}

/* Slide Carousel Frame */
.carousel-box {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 28px;
}
.deck-viewport {
    background: #0B0F19;
    border: 1px solid #1F2937;
    border-radius: 14px;
    padding: 28px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.deck-stage {
    width: 100%;
    max-width: 920px;
    min-height: 460px;
    aspect-ratio: 16 / 9;
    background: radial-gradient(circle at 80% 20%, #172033 0%, #0F172A 100%);
    border: 1px solid #1F2937;
    border-radius: 12px;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(99, 102, 241, 0.15);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 40px 48px;
    position: relative;
    overflow: hidden;
}
.deck-stage::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #6366F1, #38BDF8, #34D399);
}
.slide-top-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #1F2937;
    padding-bottom: 14px;
    margin-bottom: 24px;
}
.slide-category-tag {
    font-size: 11px;
    font-weight: 700;
    color: #818CF8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.slide-aspect-tag {
    font-size: 11px;
    color: #475569;
    font-weight: 600;
}
.slide-footer-meta {
    border-top: 1px solid #1F2937;
    padding-top: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    color: #475569;
}
.speaker-notes-box {
    width: 100%;
    max-width: 920px;
    background: #111827;
    border: 1px solid #1F2937;
    border-left: 3px solid #818CF8;
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 16px;
}

/* Streamlit Inputs Overrides */
div[data-testid="stFileUploader"] > div {
    background: #111827 !important;
    border: 1.5px dashed rgba(99, 102, 241, 0.35) !important;
    border-radius: 14px !important;
}
div[data-testid="stFileUploader"] > div:hover {
    border-color: #6366F1 !important;
}
div[data-testid="stTextInput"] input {
    background: #1F2937 !important;
    border: 1px solid #374151 !important;
    color: #F8FAFC !important;
    border-radius: 8px !important;
}
button[kind="primary"] {
    background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
    border: none !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    padding: 14px 24px !important;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35) !important;
    transition: all 0.2s ease !important;
}
button[kind="primary"]:hover {
    opacity: 0.92 !important;
    box-shadow: 0 6px 24px rgba(99, 102, 241, 0.5) !important;
}

/* Custom Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px !important;
    background-color: transparent !important;
    border-bottom: 1px solid #1F2937 !important;
    margin-bottom: 24px !important;
}
.stTabs [data-baseweb="tab"] {
    height: 44px !important;
    white-space: pre-wrap !important;
    background-color: rgba(255, 255, 255, 0.02) !important;
    border-radius: 8px 8px 0px 0px !important;
    border: 1px solid #1F2937 !important;
    border-bottom: none !important;
    color: #94A3B8 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 0 20px !important;
    transition: all 0.15s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #F8FAFC !important;
    background-color: rgba(99, 102, 241, 0.08) !important;
}
.stTabs [aria-selected="true"] {
    background-color: #111827 !important;
    color: #A5B4FC !important;
    border-color: #1F2937 !important;
    border-bottom: 2px solid #6366F1 !important;
}

/* Secondary Buttons (Slide Selectors & Nav) */
button[kind="secondary"] {
    background-color: #111827 !important;
    border: 1px solid #1F2937 !important;
    color: #CBD5E1 !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    transition: all 0.15s ease !important;
}
button[kind="secondary"]:hover {
    border-color: rgba(99, 102, 241, 0.5) !important;
    color: #F8FAFC !important;
    background-color: #1F2937 !important;
}
button[kind="secondary"]:disabled {
    opacity: 0.35 !important;
    border-color: #1F2937 !important;
}

/* Sidebar Expanders */
[data-testid="stExpander"] {
    background-color: #111827 !important;
    border: 1px solid #1F2937 !important;
    border-radius: 10px !important;
    margin-bottom: 12px !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    color: #CBD5E1 !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    padding: 10px 14px !important;
    transition: color 0.15s ease !important;
}
[data-testid="stExpander"] summary:hover {
    color: #818CF8 !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background-color: #0D1322 !important;
    border-top: 1px solid #1F2937 !important;
    padding: 14px !important;
}

/* Custom Selectbox Theme */
div[data-baseweb="select"] > div {
    background-color: #111827 !important;
    border: 1px solid #1F2937 !important;
    border-radius: 8px !important;
    color: #F8FAFC !important;
}
div[data-baseweb="select"] > div:hover {
    border-color: #6366F1 !important;
}

/* Responsive Grid Breakpoints */
@media (max-width: 1024px) {
    .kpi-row {
        grid-template-columns: repeat(2, 1fr) !important;
    }
    .insight-grid {
        grid-template-columns: 1fr !important;
    }
}
@media (max-width: 640px) {
    .kpi-row {
        grid-template-columns: 1fr !important;
    }
    .block-container {
        padding: 1rem 1rem 3rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# NAVIGATION BAR
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ap-nav">
    <div class="ap-logo-group">
        <div class="ap-logo-icon">✦</div>
        <div class="ap-logo-text">AutoPilot <span>Studio</span></div>
    </div>
    <div class="ap-tagline">Automated Analytics & Executive Slide Generation</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HERO BANNER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-box">
    <div class="hero-headline">Turn Raw Spreadsheets into Executive Board Decks</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR CONTROLS & WORKSPACE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.08);">
        <div style="width:34px;height:34px;border-radius:8px;background:linear-gradient(135deg, #6366F1, #8B5CF6);display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:800;color:#FFF;box-shadow:0 0 16px rgba(99,102,241,0.4);">✦</div>
        <div>
            <div style="font-size:16px;font-weight:800;color:#F8FAFC;letter-spacing:-0.02em;">AutoPilot <span style="background:linear-gradient(90deg,#818CF8,#C084FC);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Studio</span></div>
            <div style="font-size:11px;color:#64748B;">Workspace Controls</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Report Mode Selector
    st.markdown('<div style="font-size:11px;font-weight:700;color:#818CF8;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">1. Report Workflow Mode</div>', unsafe_allow_html=True)
    report_mode = st.selectbox(
        "Report Mode",
        ["Sales & Retail Performance", "Marketing & Ad Campaign ROI", "Operations & Expense Tracker", "Ask your own questions (any data)"],
        index=0,
        label_visibility="collapsed",
        help="Adapts KPI metrics, AI boardroom commentary, and slide structures to your specific business workflow."
    )

    current_year = datetime.date.today().year
    default_titles = {
        "Sales & Retail Performance": f"{current_year} Sales Performance Review",
        "Marketing & Ad Campaign ROI": f"{current_year} Marketing ROI & Ad Spend Review",
        "Operations & Expense Tracker": f"{current_year} Operations & Expense Report"
    }

    # 2. Data Source
    st.markdown('<div style="font-size:11px;font-weight:700;color:#818CF8;text-transform:uppercase;letter-spacing:0.06em;margin-top:14px;margin-bottom:6px;">2. Data Source (.csv, .xlsx)</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload dataset (.csv, .xlsx, .xls)",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed"
    )
    selected_sheet = 0
    if uploaded_file and uploaded_file.name.endswith((".xlsx", ".xls")):
        try:
            with pd.ExcelFile(uploaded_file) as xl:
                if len(xl.sheet_names) > 1:
                    st.markdown('<div style="font-size:11px;font-weight:700;color:#38BDF8;text-transform:uppercase;letter-spacing:0.06em;margin-top:8px;margin-bottom:4px;">Select Excel Sheet</div>', unsafe_allow_html=True)
                    selected_sheet = st.selectbox("Excel Sheet", xl.sheet_names, key="excel_sheet_select", label_visibility="collapsed")
        except Exception:
            selected_sheet = 0
    use_sample = st.checkbox("⚡ Load sample dataset", value=False)

    # 3. Presentation Title (Derived dynamically from uploaded file or report mode)
    st.markdown('<div style="font-size:11px;font-weight:700;color:#818CF8;text-transform:uppercase;letter-spacing:0.06em;margin-top:14px;margin-bottom:6px;">3. Presentation Title</div>', unsafe_allow_html=True)
    if uploaded_file:
        raw_stem = os.path.splitext(uploaded_file.name)[0]
        clean_stem = re.sub(r'[\s_\-]+', ' ', raw_stem).strip().title()
        if any(w in clean_stem.lower() for w in ["review", "report", "overview", "deck", "presentation", "analysis"]):
            suggested_title = clean_stem
        else:
            suggested_title = f"{clean_stem} Performance Review"
    else:
        suggested_title = default_titles.get(report_mode, f"{current_year} Executive Performance Review")

    # Sync title with session state when data source or mode changes
    active_source_id = uploaded_file.name if uploaded_file else f"sample_{report_mode}"
    if st.session_state.get("last_source_id") != active_source_id:
        st.session_state["last_source_id"] = active_source_id
        st.session_state["presentation_title_input"] = suggested_title

    report_title = st.text_input(
        "Presentation Title",
        value=st.session_state.get("presentation_title_input", suggested_title),
        key="presentation_title_input",
        label_visibility="collapsed"
    )

if not uploaded_file and not use_sample:
    st.info("👈 **Welcome to AutoPilot Studio!**\n\nPlease upload a dataset (.csv or .xlsx) or check **'Load sample dataset'** in the sidebar to generate your executive report.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# LOAD & PREPARE DATA
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, max_entries=8)
def load_uploaded_dataset(name: str, file_bytes: bytes, sheet=0):
    """Parse once per (file, sheet); widget clicks no longer re-read the upload."""
    from io_utils import read_tabular
    return read_tabular(name, file_bytes, sheet)

with st.spinner("Processing data engine..."):
    if use_sample or uploaded_file is None:
        from generate_data import generate_sales_data
        df = generate_sales_data()
        source_notes = []
    else:
        try:
            df, source_notes = load_uploaded_dataset(uploaded_file.name, uploaded_file.getvalue(), selected_sheet)
        except Exception as e:
            st.error(f"⚠️ **Could not read file:** {str(e)}\n\nPlease ensure your file is a valid CSV or Excel spreadsheet.")
            st.stop()

cols = df.columns.tolist()

import hashlib
from objectives_ui import (
    _sig,
    _state_reset_if_new,
    render_studio_tab,
    run_auto_expert_objectives,
    compute_objective_kpis,
    expand_dashboard_results,
    render_objective_dashboard_tab,
    build_objective_slide_previews,
)
import objectives as ob
from analysis_engine import infer_mapping, get_time_scope_options, filter_df_by_time_scope
from export_utils import generate_cleaned_workbook
from schema import PreparedFrame

obj_sig = _sig(df)
_state_reset_if_new(obj_sig)
is_obj_mode = report_mode.startswith("Ask your own questions")
has_user_objectives = len(st.session_state.get("oq_questions", [])) > 0
use_objective_dashboard = is_obj_mode or has_user_objectives

opt_cols = ["None / Not Available"] + cols
drop_dupes_opt = False
id_col_opt = None
date_col = cols[0]
revenue_col = cols[0]
profit_col = "None / Not Available"
cost_col = "None / Not Available"
conv_col = "None / Not Available"
cat_col = "None / Not Available"
region_col = "None / Not Available"

if not use_objective_dashboard:
    inferred_cols = infer_mapping(df, report_mode=report_mode)
    date_col    = inferred_cols.get("date") or cols[0]
    revenue_col = inferred_cols.get("revenue") or cols[0]
    profit_col  = inferred_cols.get("profit") or "None / Not Available"
    cost_col    = inferred_cols.get("cost") or "None / Not Available"
    conv_col    = inferred_cols.get("conversions") or "None / Not Available"
    cat_col     = inferred_cols.get("category") or "None / Not Available"
    region_col  = inferred_cols.get("region") or "None / Not Available"

# Sidebar Expanders for advanced workspace settings
with st.sidebar:
    if not use_objective_dashboard:
        with st.expander("⚙️ Verify Auto-Mapped Columns", expanded=False):
            rev_input_label = "Spend / Revenue" if "Marketing" in report_mode else ("Budget / Allocation" if "Operations" in report_mode else "Revenue Column")
            date_col    = st.selectbox("Date Column", cols, index=cols.index(date_col))
            revenue_col = st.selectbox(rev_input_label, cols, index=cols.index(revenue_col))
            profit_input_label = "Return Value (optional, for ROAS)" if "Marketing" in report_mode else ("Actual Expenses" if "Operations" in report_mode else "Profit Column")
            profit_col  = st.selectbox(profit_input_label, opt_cols, index=opt_cols.index(profit_col))
            if "Sales" in report_mode:
                cost_col = st.selectbox("Cost Column", opt_cols, index=opt_cols.index(cost_col))
            else:
                cost_col = "None / Not Available"
            if "Marketing" in report_mode:
                conv_col = st.selectbox("Conversions Column", opt_cols, index=opt_cols.index(conv_col))
            cat_input_label = "Channel / Campaign" if "Marketing" in report_mode else ("Department / Unit" if "Operations" in report_mode else "Category Column")
            reg_input_label = "Market / Geo" if "Marketing" in report_mode else ("Facility / Location" if "Operations" in report_mode else "Region Column")
            cat_col     = st.selectbox(cat_input_label, opt_cols, index=opt_cols.index(cat_col))
            region_col  = st.selectbox(reg_input_label, opt_cols, index=opt_cols.index(region_col))
            st.markdown("**Duplicates**")
            drop_dupes_opt = st.checkbox("Remove exact duplicate rows", value=False,
                                         help="Off by default: identical rows are often genuine repeat transactions.")
            id_col_choice = st.selectbox("Unique ID column (optional)", opt_cols, index=0,
                                         help="If your file has an order/transaction ID, rows with a repeated ID are removed.")
            id_col_opt = None if id_col_choice == "None / Not Available" else id_col_choice

    with st.expander("🤖 AI Intelligence (Gemini)", expanded=False):
        gemini_api_key_input = st.text_input(
            "Gemini API Key (Optional)",
            type="password",
            placeholder="AIzaSy... (leave blank for template)",
            help="Paste your Gemini API key to generate live tailored executive narratives and speaker scripts. Key is stored only in session state."
        )
        if "ai_calls_count" not in st.session_state:
            st.session_state.ai_calls_count = 0
        MAX_AI_CALLS = 10

        from ai_narrator import get_gemini_api_key
        # SERVER key safety: set REQUIRE_USER_KEY=1 to force visitors to bring their own key.
        # Otherwise the shared server key is capped process-wide per day (refresh cannot reset it).
        REQUIRE_USER_KEY = os.environ.get("REQUIRE_USER_KEY", "").strip().lower() in ("1", "true", "yes")
        MAX_SERVER_AI_CALLS_PER_DAY = int(os.environ.get("MAX_SERVER_AI_CALLS_PER_DAY", "50"))

        @st.cache_resource
        def _server_ai_budget():
            return {"day": None, "used": 0}

        def _server_budget_left() -> int:
            b = _server_ai_budget()
            today = datetime.date.today().isoformat()
            if b["day"] != today:
                b["day"], b["used"] = today, 0
            return MAX_SERVER_AI_CALLS_PER_DAY - b["used"]

        user_key = gemini_api_key_input.strip() if gemini_api_key_input else ""
        using_server_key = False
        if user_key:
            active_api_key = user_key
        elif not REQUIRE_USER_KEY and _server_budget_left() > 0:
            active_api_key = get_gemini_api_key()
            using_server_key = bool(active_api_key)
        else:
            active_api_key = None
            if REQUIRE_USER_KEY or get_gemini_api_key():
                st.caption("Enter your own Gemini API key to enable AI commentary." if REQUIRE_USER_KEY else "Shared AI quota used up for today. Enter your own key to continue.")

        if active_api_key:
            st.caption(f"✦ Session AI Calls: {st.session_state.ai_calls_count}/{MAX_AI_CALLS}")
            gen_ai_clicked = st.button("✨ Generate AI Commentary", help="Generate customized LLM-powered narrative & speaker notes.", use_container_width=True)
        else:
            gen_ai_clicked = False
            st.caption(f"✦ Using built-in deterministic {report_mode} executive commentary.")

    with st.expander("🎨 Brand Kit & White-Labeling", expanded=False):
        currency_options = ["$", "₵", "₦", "£", "€", "None"]
        currency_symbol = st.selectbox("Currency Symbol", currency_options, index=0, help="Currency symbol used across KPI cards, chart axes, and presentation slides.")
        curr_sym = "" if currency_symbol == "None" else currency_symbol
        brand_name = st.text_input("Brand / Organization Name", value="", placeholder="e.g. Acme Corp (leave blank for AutoPilot)", help="Custom organization name displayed on Slide 1.")
        brand_color = st.color_picker("Brand Accent Color", value="#6366F1", help="Select corporate accent color to theme the PowerPoint presentation.")
        logo_file = st.file_uploader("Brand Logo (.png, .jpg)", type=["png", "jpg", "jpeg"], help="Optional: Upload company logo for slide headers and cover.")


def render_slide_carousel(slides: list):
    """Render the shared 16:9 Linear Obsidian slide preview carousel + Previous/Next buttons."""
    if "slide_idx" not in st.session_state:
        st.session_state.slide_idx = 0
    st.session_state.slide_idx = max(0, min(st.session_state.slide_idx, len(slides) - 1))

    tab_cols = st.columns(len(slides))
    for i, s in enumerate(slides):
        with tab_cols[i]:
            if st.button(f"{s['icon']} {s['num']} · {s['name']}", key=f"s_{i}", use_container_width=True,
                         type="primary" if i == st.session_state.slide_idx else "secondary"):
                st.session_state.slide_idx = i
                st.rerun()

    curr_s = slides[st.session_state.slide_idx]
    st.markdown(f'''
    <div class="deck-viewport">
        <div class="deck-stage">
            <div class="slide-top-meta">
                <span class="slide-category-tag">{curr_s["tag"]}</span>
            </div>
            {curr_s["html"]}
        </div>
        <div class="speaker-notes-box">
            <div style="font-size:11px;font-weight:700;color:#818CF8;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">
                🎤 Speaker Notes
            </div>
            <div style="font-size:13px;color:#CBD5E1;line-height:1.6;font-style:italic;">
                "{h(curr_s["notes"])}"
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    c_prev, c_space, c_next = st.columns([1, 4, 1])
    with c_prev:
        if st.button("◀ Previous Slide", use_container_width=True, disabled=(st.session_state.slide_idx == 0)):
            st.session_state.slide_idx -= 1
            st.rerun()
    with c_next:
        if st.button("Next Slide ▶", use_container_width=True, disabled=(st.session_state.slide_idx == len(slides) - 1)):
            st.session_state.slide_idx += 1
            st.rerun()
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# OBJECTIVE-DRIVEN & AUTO-EXPERT UNIFIED 3-TAB FLOW
# ─────────────────────────────────────────────────────────────────────────────
if use_objective_dashboard:
    tab_dash, tab_deck, tab_obj = st.tabs([
        "📊 Executive Dashboard",
        "🖥️ Slide Deck Preview & Export",
        "🎯 Objectives & Data Studio",
    ])

    # Run Tab 3 controls first in code order so policy/question edits apply immediately in this rerun
    with tab_obj:
        sig, prep, handled, hp, obj_specs, user_results, is_auto = render_studio_tab(df, currency=curr_sym)

    # Time Scope filtering on PreparedFrame (when a date column exists)
    if hp.schema.date and hp.schema.date in hp.df.columns:
        scope_options = get_time_scope_options(pd.DataFrame({"Date": hp.df[hp.schema.date]}))
    else:
        scope_options = [{"id": "all", "label": "Full Dataset"}]
    scope_labels = [s["label"] for s in scope_options]
    scope_id_map = {s["label"]: s["id"] for s in scope_options}
    active_scope_label = st.session_state.get("global_time_scope", scope_labels[0] if scope_labels else "Full Dataset")
    if active_scope_label not in scope_id_map:
        active_scope_label = scope_labels[0] if scope_labels else "Full Dataset"
    active_scope_id = scope_id_map.get(active_scope_label, "all")
    sel_scope_idx = scope_labels.index(active_scope_label) if active_scope_label in scope_labels else 0

    scoped_hp = hp
    active_scope_name = "Full Period"
    if active_scope_id != "all" and hp.schema.date and hp.schema.date in hp.df.columns:
        tmp_dates = pd.DataFrame({"Date": hp.df[hp.schema.date]}, index=hp.df.index)
        filtered_idx_df, active_scope_name = filter_df_by_time_scope(tmp_dates, active_scope_id)
        if filtered_idx_df is not None and not filtered_idx_df.empty:
            scoped_hp = PreparedFrame(
                df=hp.df.loc[filtered_idx_df.index].reset_index(drop=True),
                schema=hp.schema, log=hp.log, quarantine=hp.quarantine,
            )
        else:
            active_scope_id = "all"

    if is_auto:
        active_results = run_auto_expert_objectives(scoped_hp, currency=curr_sym, limit=4)
    elif active_scope_id != "all":
        active_results = ob.run_objectives(obj_specs, scoped_hp, curr_sym, st.session_state["oq_accept"])
    else:
        active_results = user_results

    obj_kpis = compute_objective_kpis(active_results, scoped_hp, currency=curr_sym, is_auto=is_auto)
    dashboard_results = expand_dashboard_results(active_results, scoped_hp, currency=curr_sym, is_auto=is_auto)
    obj_wb_key = ("obj_wb", obj_sig, curr_sym, active_scope_id, len(hp.df), tuple(hp.log))
    obj_stem = os.path.splitext(uploaded_file.name)[0].strip().replace(" ", "_") if uploaded_file else report_title.strip().replace(" ", "_")

    def _render_obj_clean_btn(prefix):
        if st.session_state.get("clean_wb_key") == obj_wb_key and st.session_state.get("clean_wb_bytes"):
            st.download_button(
                label="📥 Download Cleaned Workbook (.xlsx)",
                data=st.session_state["clean_wb_bytes"],
                file_name=f"{obj_stem}_Cleaned.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key=f"{prefix}_dl",
            )
        elif st.button("🧾 Prepare Cleaned Workbook (.xlsx)", use_container_width=True, key=f"{prefix}_prep"):
            with st.spinner("Building workbook..."):
                hyg_meta = {"clean_row_count": len(hp.df), "audit_log": hp.log, "health_score": 100}
                st.session_state["clean_wb_bytes"] = generate_cleaned_workbook(
                    scoped_hp.df, hyg_meta, hp.quarantine if hp.quarantine is not None else pd.DataFrame(), currency_symbol=curr_sym
                )
                st.session_state["clean_wb_key"] = obj_wb_key
            st.rerun()

    with tab_dash:
        render_objective_dashboard_tab(
            hp=scoped_hp,
            results=dashboard_results,
            kpi_cards=obj_kpis,
            scope_labels=scope_labels,
            sel_scope_idx=sel_scope_idx,
            is_auto=is_auto,
            currency=curr_sym,
            brand_color=brand_color,
            render_clean_btn_fn=_render_obj_clean_btn,
        )

    with tab_deck:
        import base64
        logo_b64 = f"data:image/png;base64,{base64.b64encode(logo_file.getvalue()).decode()}" if ('logo_file' in locals() and logo_file) else None
        export_title = f"{report_title} ({active_scope_name})" if active_scope_id != "all" else report_title
        mode_lbl = "Auto-Expert Analysis" if is_auto else "Objective-Driven Analysis"
        obj_slides = build_objective_slide_previews(
            results=dashboard_results, kpi_cards=obj_kpis, prepared=scoped_hp,
            title=export_title, mode_label=mode_lbl, brand_color=brand_color, logo_b64=logo_b64,
        )
        render_slide_carousel(obj_slides)

        deck_key = (
            "obj_deck", obj_sig, active_scope_id, curr_sym, export_title, brand_color, brand_name,
            logo_file.name if logo_file else None,
            tuple((r.spec.id, r.spec.text, r.finding.status, r.finding.headline) for r in dashboard_results),
            tuple((k["label"], k["value"]) for k in obj_kpis),
        )
        answered_objs = [r for r in dashboard_results if r.finding.status in ("ok", "caution")]
        safe_title = export_title.replace(" ", "_")
        if not answered_objs:
            st.caption("Answer at least one objective to export a PowerPoint deck.")
        elif st.session_state.get("oq_deck", {}).get("key") == deck_key:
            col_dl, col_rb = st.columns([3, 1])
            with col_dl:
                st.download_button(
                    label="📥  Download Executive PowerPoint Deck (.pptx)",
                    data=st.session_state["oq_deck"]["bytes"],
                    file_name=f"{safe_title}.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True, type="primary", key="oq_dl_deck_unified",
                )
            with col_rb:
                if st.button("🔄 Recompile", use_container_width=True, key="oq_recomp_unified"):
                    st.session_state.pop("oq_deck", None)
                    st.rerun()
        elif st.button("🚀  Generate Executive PowerPoint Deck (.pptx)", type="primary", use_container_width=True, key="oq_gen_deck_unified"):
            with st.spinner("🎨 Rendering charts and compiling PowerPoint deck..."):
                import tempfile
                from objective_deck import build_objective_deck
                with tempfile.TemporaryDirectory() as tmp_dir:
                    l_path = None
                    if logo_file:
                        l_ext = logo_file.name.split(".")[-1]
                        l_path = os.path.join(tmp_dir, f"brand_logo.{l_ext}")
                        with open(l_path, "wb") as lf:
                            lf.write(logo_file.getbuffer())
                    p_path = build_objective_deck(
                        dashboard_results, title=export_title, quality_notes=hp.log,
                        brand_color=brand_color, brand_name=brand_name or None,
                        logo_path=l_path, output_dir=tmp_dir, kpis=obj_kpis, currency=curr_sym,
                    )
                    with open(p_path, "rb") as pf:
                        st.session_state["oq_deck"] = {"key": deck_key, "bytes": pf.read()}
            st.rerun()

    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# COMPUTE METRICS VIA ANALYSIS ENGINE (Single Source of Truth, Cached)
# ─────────────────────────────────────────────────────────────────────────────
import hashlib
from analysis_engine import build_report_from_df

col_mapping = {
    "date": date_col,
    "revenue": revenue_col,
    "profit": profit_col if profit_col != "None / Not Available" else None,
    "cost": cost_col if cost_col != "None / Not Available" else None,
    "conversions": conv_col if ("Marketing" in report_mode and conv_col != "None / Not Available") else None,
    "category": cat_col if cat_col != "None / Not Available" else None,
    "region": region_col if region_col != "None / Not Available" else None,
    "product": "Product" if "Product" in df.columns else (cat_col if cat_col != "None / Not Available" else None),
}

# Deterministic content hash ensures uploading a new dataset with identical column names
# recomputes fresh metrics while keeping slide carousel navigation instant.
ENGINE_VERSION = "v3.2_adaptive_horizons_cachebuster"
data_hash = hashlib.md5(pd.util.hash_pandas_object(df, index=True).values).hexdigest()
data_signature = f"{data_hash}_{ENGINE_VERSION}"

@st.cache_data(show_spinner=False)
def get_cached_report(_df, mapping, mode, curr, data_signature, drop_dupes=False, id_col=None, notes=()):
    return build_report_from_df(_df, mapping=mapping, report_mode=mode, currency_symbol=curr,
                                drop_exact_duplicates=drop_dupes, id_column=id_col, source_notes=list(notes))

from export_utils import generate_cleaned_workbook

try:
    report_data = get_cached_report(df, col_mapping, report_mode, curr_sym, data_signature, drop_dupes_opt, id_col_opt, tuple(source_notes))
except Exception as e:
    st.error(f"⚠️ **Could not process this spreadsheet:** {str(e)}\n\nPlease ensure your Date and Revenue columns contain valid values.")
    st.stop()

clean_export_df = report_data.get("df", df)
quarantined_df  = report_data.get("quarantined_df", pd.DataFrame())
safe_filename   = report_title.strip().replace(" ", "_")
if uploaded_file:
    orig_stem = os.path.splitext(uploaded_file.name)[0].strip().replace(" ", "_")
    clean_export_filename = f"{orig_stem}_Cleaned.xlsx"
else:
    clean_export_filename = f"{safe_filename}_Cleaned.xlsx"
wb_key = ("clean_wb", data_signature, curr_sym, drop_dupes_opt, id_col_opt, repr(sorted((col_mapping or {}).items())), report_mode)

def render_clean_workbook_button(prefix):
    """Build the workbook only when asked (it is slow for big files), then offer the download."""
    if st.session_state.get("clean_wb_key") == wb_key and st.session_state.get("clean_wb_bytes"):
        st.download_button(
            label="📥 Download Cleaned Workbook (.xlsx)",
            data=st.session_state["clean_wb_bytes"],
            file_name=clean_export_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, key=f"{prefix}_dl",
            help="3-tab Excel file: Cleaned Data, Audit Trail, and Quarantined Rows.",
        )
    elif st.button("🧾 Prepare Cleaned Workbook (.xlsx)", use_container_width=True, key=f"{prefix}_prep"):
        with st.spinner("Building workbook..."):
            st.session_state["clean_wb_bytes"] = generate_cleaned_workbook(
                clean_export_df, report_data.get("hygiene", {}), quarantined_df, currency_symbol=curr_sym)
            st.session_state["clean_wb_key"] = wb_key
        st.rerun()

kpis      = report_data["kpis"]
monthly   = report_data["monthly"]
category  = report_data["category"]
region_df = report_data["region"]
insights  = report_data["insights"]
hygiene   = report_data.get("hygiene", {})
anomalies = insights.get("anomalies", [])

# Render Data Hygiene Audit Log in Sidebar
with st.sidebar:
    with st.expander("🛡️ Data Hygiene & Audit Trail", expanded=False):
        score = hygiene.get('health_score', 100)
        status = hygiene.get('health_status', 'No issues found')
        status_color = "#34D399" if score >= 98 else "#FBBF24"
        retention = hygiene.get('rows_retained_pct', 100.0)
        dropped_count = hygiene.get('dropped_rows_count', 0)
        dropped_line = f"<div>• Dropped blank/unparseable rows: <strong>{dropped_count:,}</strong></div>" if dropped_count > 0 else ""
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
            <span style="font-size:11px;font-weight:700;color:#94A3B8;text-transform:uppercase;">Data Integrity</span>
            <span style="font-size:11px;font-weight:700;color:{status_color};background:rgba(16,185,129,0.12);padding:2px 8px;border-radius:10px;border:1px solid rgba(16,185,129,0.25);">✦ {status} ({score}%)</span>
        </div>
        <div style="font-size:12px;color:#CBD5E1;line-height:1.6;margin-bottom:10px;">
            <div>• <strong>{hygiene.get('clean_row_count', 0):,}</strong> records parsed ({retention}% retention)</div>
            {dropped_line}
            <div>• Coverage: <strong>{hygiene.get('date_range', 'Validated')}</strong></div>
            <div>• Sanitized formatters/nulls: <strong>{hygiene.get('currency_symbols_stripped', 0) + hygiene.get('missing_values_imputed', 0):,}</strong></div>
        </div>
        """, unsafe_allow_html=True)
        if hygiene.get("audit_log"):
            st.markdown('<div style="font-size:11px;font-weight:700;color:#818CF8;margin-bottom:6px;text-transform:uppercase;">Automated Audit Trail:</div>', unsafe_allow_html=True)
            for step in hygiene["audit_log"]:
                st.markdown(f'<div style="font-size:11px;color:#94A3B8;margin-bottom:3px;">✔ {step}</div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        render_clean_workbook_button("sb")

clean_df = report_data.get("df", df)
from analysis_engine import filter_df_by_time_scope, compute_kpis, category_breakdown, region_breakdown, get_time_scope_options, build_scoped_report

time_scopes = report_data.get("time_scopes", {})
# Resolve scope options dynamically from clean_df if not yet in cached report_data
scope_options = time_scopes.get("scope_options") or get_time_scope_options(clean_df)
time_scopes["scope_options"] = scope_options
scope_labels = [s["label"] for s in scope_options]
scope_id_map = {s["label"]: s["id"] for s in scope_options}

active_scope_label = st.session_state.get("global_time_scope", scope_labels[0] if scope_labels else "Full Dataset")
if active_scope_label not in scope_id_map:
    active_scope_label = scope_labels[0] if scope_labels else "Full Dataset"
active_scope_id = scope_id_map.get(active_scope_label, "all")

scoped_df, active_scope_name = filter_df_by_time_scope(clean_df, active_scope_id)
if scoped_df is None or scoped_df.empty:
    scoped_df = clean_df
    active_scope_id = "all"
    active_scope_name = "Full Period"

# One scoped report drives EVERYTHING downstream (cards, takeaways, narrative, preview, export).
# The cached full-dataset report is never mutated.
base_report = report_data
report_data = build_scoped_report(base_report, active_scope_id, curr_sym)
kpis      = report_data["kpis"]
monthly   = report_data["monthly"]
category  = report_data["category"]
region_df = report_data["region"]
insights  = report_data["insights"]
anomalies = insights.get("anomalies", [])
# Per-view copy that the trend drill-down may adjust (granularity/year) without touching report_data
view_report = {**report_data, "insights": dict(report_data["insights"])}

has_profit    = kpis.get("has_profit", True)
total_revenue = kpis["total_revenue"]
total_profit  = kpis["total_profit"]
total_cost    = kpis["total_cost"]
total_orders  = kpis["total_orders"]
profit_margin = kpis["profit_margin"]
avg_order_val = kpis["avg_order_value"]

best_month  = insights["best_month"]
worst_month = insights["worst_month"]
top_cat     = insights["top_category"]
top_region  = insights["top_region"]
mom_avg     = insights["avg_mom_growth"]  # may be None when history is too short
cat_col     = "Category"
region_col  = "Region"
meta        = report_data.get("meta", {})

def fmt(v):
    if v is None: return "N/A"
    prefix = curr_sym
    abs_v = abs(v)
    if abs_v >= 1_000_000_000_000:
        return f"{prefix}{v/1_000_000_000_000:.2f}T"
    elif abs_v >= 1_000_000_000:
        return f"{prefix}{v/1_000_000_000:.2f}B"
    elif abs_v >= 1_000_000:
        return f"{prefix}{v/1_000_000:.2f}M"
    elif abs_v >= 1_000:
        return f"{prefix}{v/1_000:.1f}K"
    return f"{prefix}{v:,.0f}"

profit_display = fmt(total_profit) if has_profit and total_profit is not None else "Not Available"
profit_pill    = meta.get("profit_sub", "After All Costs") if has_profit and total_profit is not None else "Allocation Mode"

# True mode-specific efficiency metric display (Margin % / ROAS / Budget Utilization)
margin_display = kpis.get("efficiency_display") or (f"{profit_margin:.1f}%" if profit_margin is not None else "N/A")
margin_pill    = kpis.get("efficiency_status") or ("Target: >35.0%" if (profit_margin or 0) >= 35.0 else "Below 35% Target")
margin_pill_class = kpis.get("efficiency_pill_class") or ("pill-purple" if (profit_margin or 0) >= 35.0 else "pill-amber")

# True CMGR with dynamic directional arrow or scope badge
if active_scope_id != "all":
    growth_label = f"🔭 {active_scope_name}"
    growth_pill_class = "pill-blue"
    growth_arrow = "↑"
else:
    growth_label = insights.get("growth_label") or "Not enough history"
    growth_arrow = insights.get("growth_arrow", "")
    growth_pill_class = "pill-amber" if growth_arrow == "↓" else "pill-blue"

# ─────────────────────────────────────────────────────────────────────────────
# AI NARRATIVE GENERATION (On-Demand & Session Cached)
# ─────────────────────────────────────────────────────────────────────────────
import ai_narrator
from ai_narrator import generate_narrative, get_deterministic_fallback

if "cached_ai_narratives" not in st.session_state:
    st.session_state.cached_ai_narratives = {}

# Narrative is only reused when EVERYTHING that shaped it is identical
narrative_key = (
    data_hash, report_mode, active_scope_id, curr_sym, report_title,
    hashlib.md5(repr(sorted((col_mapping or {}).items())).encode()).hexdigest(),
)

# Check if user explicitly triggered Gemini AI commentary
if 'gen_ai_clicked' in locals() and gen_ai_clicked and active_api_key:
    if st.session_state.ai_calls_count >= MAX_AI_CALLS:
        st.warning(f"⚠️ Session AI call limit reached ({MAX_AI_CALLS} calls). Using existing commentary.")
    else:
        with st.spinner(f"🧠 Synthesizing executive narrative with Gemini ({report_mode})..."):
            st.session_state.ai_calls_count += 1
            if using_server_key:
                _server_ai_budget()["used"] += 1
            ai_result = generate_narrative(
                report_data, report_title=report_title, report_mode=report_mode,
                api_key=active_api_key, currency_symbol=curr_sym
            )
            st.session_state.cached_ai_narratives[narrative_key] = ai_result
            st.toast("✨ Gemini executive narrative & speaker notes generated!", icon="🧠")

# Resolve active narrative: user-generated AI narrative for this data hash if available, else deterministic template
if narrative_key in st.session_state.cached_ai_narratives:
    narrative = st.session_state.cached_ai_narratives[narrative_key]
else:
    narrative = get_deterministic_fallback(
        report_data, report_title=report_title, report_mode=report_mode, currency_symbol=curr_sym
    )

speaker_notes = narrative.get("speaker_notes", {})
recs          = narrative.get("recommendations", [])
takeaways     = narrative.get("takeaways", [])

# ─────────────────────────────────────────────────────────────────────────────
# WORKSPACE TABS: EXECUTIVE DASHBOARD & SLIDE DECK
# ─────────────────────────────────────────────────────────────────────────────
# Synchronize session state across tab boundaries with resilient defaults
trend_style  = st.session_state.get("ctrl_trend", "Grouped Bars")
cat_style    = st.session_state.get("ctrl_cat", "Horizontal Bar")
region_style = st.session_state.get("ctrl_region", "Donut")
top_metric   = st.session_state.get("ctrl_metric", "Revenue")
top_n        = st.session_state.get("ctrl_count", 5)
prod_rank    = report_data.get('top_products')

tab_dash, tab_deck, tab_obj = st.tabs([
    "📊 Executive Dashboard",
    "🖥️ Slide Deck Preview & Export",
    "🎯 Objectives & Data Studio",
])

with tab_obj:
    render_studio_tab(df, currency=curr_sym)

with tab_dash:
    # ─────────────────────────────────────────────────────────────────────────────
    # EXECUTIVE TIME SCOPE & DATA STATUS BAR
    # ─────────────────────────────────────────────────────────────────────────────
    status_suffix = "Usable" if hygiene.get("health_score", 100) == 100 else "Usable (see audit)"
    hygiene_pill = f'<span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:10px;background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.25);color:#34D399;margin-left:8px;">✔ {hygiene.get("clean_row_count", len(df)):,} Records {status_suffix}</span>'

    scope_options = time_scopes.get("scope_options") or get_time_scope_options(clean_df)
    scope_labels = [s["label"] for s in scope_options]
    sel_idx = scope_labels.index(active_scope_label) if active_scope_label in scope_labels else 0

    col_kpi_head, col_scope, col_kpi_dl = st.columns([2.6, 1.1, 0.9])
    with col_kpi_head:
        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;padding-top:4px;"><span style="font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);color:#A5B4FC;">{h(report_mode)}</span>{hygiene_pill}</div>', unsafe_allow_html=True)
    with col_scope:
        sel_scope_label = st.selectbox(
            "Executive Time Scope",
            scope_labels,
            index=sel_idx,
            key="global_time_scope",
            label_visibility="collapsed",
            help="Filter entire dashboard (KPIs, Charts, Breakdowns, & Slide Deck) by time horizon"
        )
    with col_kpi_dl:
        render_clean_workbook_button("dash")
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    if narrative.get("executive_summary"):
        surge_badge_inline = ""
        if anomalies:
            top_a = anomalies[0]
            anom_color = "#34D399" if top_a["type"] == "Surge" else "#F87171"
            anom_bg = "rgba(16, 185, 129, 0.12)" if top_a["type"] == "Surge" else "rgba(248, 113, 113, 0.12)"
            anom_border = "rgba(16, 185, 129, 0.3)" if top_a["type"] == "Surge" else "rgba(248, 113, 113, 0.3)"
            surge_badge_inline = (
                f'<span style="margin-left:8px;display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:6px;background:{anom_bg};border:1px solid {anom_border};font-size:11.5px;color:#F8FAFC;font-weight:600;">'
                f'<span style="color:{anom_color};">⚡ {h(top_a["type"].upper())}:</span> '
                f'{h(top_a["period"])} {top_a["pct_diff_mean"]:+.1f}% vs. baseline'
                f'</span>'
            )

        briefing_html = (
            f'<div style="background:linear-gradient(135deg, rgba(99,102,241,0.08), rgba(56,189,248,0.04));border:1px solid rgba(99,102,241,0.22);border-radius:8px;padding:12px 18px;margin-bottom:18px;font-size:13px;color:#E2E8F0;line-height:1.6;">'
            f'<span style="font-weight:700;color:#A5B4FC;margin-right:6px;">✦ EXECUTIVE BRIEFING:</span>'
            f'{h(narrative["executive_summary"])}'
            f'{surge_badge_inline}'
            f'</div>'
        )
        st.markdown(briefing_html, unsafe_allow_html=True)

    kpi_rev_lbl = meta.get("rev_label", "Gross Revenue")
    kpi_profit_lbl = meta.get("profit_label", "Net Profit")
    kpi_margin_lbl = meta.get("margin_label", "Profit Margin")
    kpi_vol_lbl = meta.get("volume_label", "Total Volume")
    kpi_aov_lbl = meta.get("aov_label", "AOV")

    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-label">{kpi_rev_lbl}</div>
            <div class="kpi-value">{fmt(total_revenue)}</div>
            <div class="kpi-pill {growth_pill_class}">{growth_label}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">{kpi_profit_lbl}</div>
            <div class="kpi-value">{profit_display}</div>
            <div class="kpi-pill pill-green">{profit_pill}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">{kpi_margin_lbl}</div>
            <div class="kpi-value">{margin_display}</div>
            <div class="kpi-pill {margin_pill_class}">{margin_pill}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">{kpi_vol_lbl}</div>
            <div class="kpi-value">{total_orders:,}</div>
            <div class="kpi-pill pill-amber">{kpi_aov_lbl}: {fmt(avg_order_val)}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────────
    # HIGH-DENSITY PLOTLY CHARTS (Dark Neon Palette + 1-Click Swappable Views)
    # ─────────────────────────────────────────────────────────────────────────────
    DARK_BG    = "#111827"
    GRID_COLOR = "#1F2937"
    TEXT_COLOR = "#94A3B8"
    PALETTE    = ["#6366F1", "#38BDF8", "#818CF8", "#0EA5E9", "#A5B4FC", "#64748B"]

    def style_chart(fig, title=None, n_bars=None, tickangle=None):
        bot_margin = 55 if (tickangle is not None and tickangle != 0) else 36
        fig.update_layout(
            paper_bgcolor=DARK_BG,
            plot_bgcolor=DARK_BG,
            font=dict(family="Plus Jakarta Sans", color=TEXT_COLOR),
            title=None,
            margin=dict(l=40, r=20, t=16, b=bot_margin),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_COLOR)),
        )
        x_kwargs = dict(showgrid=False, linecolor=GRID_COLOR, tickcolor=GRID_COLOR)
        if tickangle is not None:
            x_kwargs["tickangle"] = tickangle
        elif n_bars is None or n_bars <= 14:
            x_kwargs["tickangle"] = 0
        fig.update_xaxes(**x_kwargs)
        fig.update_yaxes(showgrid=True, gridcolor=GRID_COLOR, linecolor=GRID_COLOR)
        return fig

    import plotly.express as px

    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        time_scopes = report_data.get("time_scopes", {})
        detected_years = time_scopes.get("years", [])
        is_multi_year = time_scopes.get("is_multi_year", False)

        if is_multi_year:
            c1_head, c1_yr, c1_gran, c1_ctrl = st.columns([1.5, 1.0, 1.25, 1.25])
            with c1_head:
                st.markdown('<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">Performance Trajectory</div>', unsafe_allow_html=True)
            with c1_yr:
                year_opts = ["All Years"] + [str(y) for y in detected_years]
                sel_year_str = st.selectbox("Year", year_opts, key="drill_year", label_visibility="collapsed")
                target_yr = None if sel_year_str == "All Years" else int(sel_year_str)
            with c1_gran:
                if target_yr is not None:
                    gran_opts = ["Quarterly", "Monthly", "Weekly", "Daily"]
                else:
                    gran_opts = ["Yearly", "Quarterly", "Monthly", "Weekly", "Daily"]
                sel_gran = st.selectbox("Granularity", gran_opts, index=1 if "Monthly" in gran_opts else 0, key="drill_gran", label_visibility="collapsed")
            with c1_ctrl:
                trend_style = st.selectbox("Style", ["Grouped Bars", "Line & Area", "Growth %"], key="ctrl_trend", label_visibility="collapsed")
        else:
            target_yr = detected_years[0] if detected_years else datetime.date.today().year
            c1_head, c1_gran, c1_ctrl = st.columns([1.8, 1.3, 1.3])
            with c1_head:
                st.markdown('<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">Performance Trajectory</div>', unsafe_allow_html=True)
            with c1_gran:
                gran_opts = ["Quarterly", "Monthly", "Weekly", "Daily"]
                sel_gran = st.selectbox("Granularity", gran_opts, index=1, key="drill_gran", label_visibility="collapsed")
            with c1_ctrl:
                trend_style = st.selectbox("Style", ["Grouped Bars", "Line & Area", "Growth %"], key="ctrl_trend", label_visibility="collapsed")

        from analysis_engine import compute_adaptive_time_series
        active_series, active_insights = compute_adaptive_time_series(
            scoped_df,
            target_year=target_yr,
            granularity=sel_gran,
            has_profit=has_profit,
            currency_symbol=curr_sym
        )
        view_report["monthly"] = active_series
        view_report["insights"].update(active_insights)
        monthly = active_series

        chart1_display_title = active_insights.get("trend_title", "Performance Trajectory")

        fig1 = go.Figure()
        if trend_style == "Line & Area":
            fig1.add_trace(go.Scatter(
                x=monthly["Month_Label"], y=monthly["Revenue"],
                mode="lines+markers", name="Revenue",
                line=dict(color="#6366F1", width=3),
                marker=dict(size=7, color="#6366F1"),
                fill="tozeroy", fillcolor="rgba(99, 102, 241, 0.12)",
            ))
            if has_profit:
                fig1.add_trace(go.Scatter(
                    x=monthly["Month_Label"], y=monthly["Profit"],
                    mode="lines+markers", name="Profit",
                    line=dict(color="#34D399", width=2.5),
                    marker=dict(size=6, color="#34D399"),
                ))
            fig1.update_yaxes(tickprefix=curr_sym, tickformat=",.0f")
            st.plotly_chart(style_chart(fig1, chart1_display_title, n_bars=len(monthly)), use_container_width=True)
        elif trend_style == "Growth %":
            growth_colors = ["#34D399" if v >= 0 else "#F87171" for v in monthly["MoM_Growth"].fillna(0)]
            fig1.add_trace(go.Bar(
                x=monthly["Month_Label"], y=monthly["MoM_Growth"],
                marker_color=growth_colors,
                text=[f"{v:+.1f}%" if not pd.isna(v) else "0.0%" for v in monthly["MoM_Growth"]],
                textposition="outside", textfont=dict(color=TEXT_COLOR, size=10),
            ))
            fig1.update_yaxes(ticksuffix="%")
            growth_header = f"{active_insights.get('growth_rate_metric', 'Period')} Velocity (%)"
            st.plotly_chart(style_chart(fig1, growth_header, n_bars=len(monthly)), use_container_width=True)
        else:
            fig1.add_trace(go.Bar(
                x=monthly["Month_Label"], y=monthly["Revenue"],
                name="Revenue", marker_color="#6366F1", opacity=0.92
            ))
            if has_profit:
                fig1.add_trace(go.Bar(
                    x=monthly["Month_Label"], y=monthly["Profit"],
                    name="Profit", marker_color="#34D399", opacity=0.92
                ))
                fig1.update_layout(barmode="group")
            fig1.update_yaxes(tickprefix=curr_sym, tickformat=",.0f")
            st.plotly_chart(style_chart(fig1, chart1_display_title, n_bars=len(monthly)), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        c2_head, c2_ctrl = st.columns([1.8, 1.3])
        with c2_head:
            st.markdown(f'<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">Category Portfolio</div>', unsafe_allow_html=True)
        with c2_ctrl:
            cat_style = st.selectbox("Style", ["Horizontal Bar", "Treemap", "Donut"], key="ctrl_cat", label_visibility="collapsed")

        if cat_style == "Treemap":
            color_col = "Margin_%" if has_profit else "Revenue"
            fig2 = px.treemap(
                category, path=[cat_col], values="Revenue",
                color=color_col, color_continuous_scale=["#1E1B4B", "#312E81", "#4F46E5", "#38BDF8"]
            )
            fig2.update_layout(
                paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
                font=dict(family="Plus Jakarta Sans", color=TEXT_COLOR),
                margin=dict(l=20, r=20, t=16, b=20),
            )
            st.plotly_chart(fig2, use_container_width=True)
        elif cat_style == "Donut":
            fig2 = go.Figure(go.Pie(
                labels=category[cat_col], values=category["Revenue"],
                hole=0.5, marker=dict(colors=PALETTE[:len(category)], line=dict(color=DARK_BG, width=2)),
                textinfo="label+percent", textfont=dict(color="#F8FAFC", size=10),
            ))
            fig2.update_layout(
                paper_bgcolor=DARK_BG,
                margin=dict(l=20, r=20, t=16, b=20),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_COLOR)),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            bar_text = [f"{curr_sym}{v:,.0f}  ({m:.1f}%)" if has_profit else f"{curr_sym}{v:,.0f}" for v, m in zip(category["Revenue"], category["Margin_%"])]
            fig2 = go.Figure(go.Bar(
                x=category["Revenue"], y=category[cat_col], orientation="h",
                marker_color=PALETTE[:len(category)],
                text=bar_text,
                textposition="outside", textfont=dict(color=TEXT_COLOR, size=11),
            ))
            fig2.update_xaxes(tickprefix=curr_sym, tickformat=",.0f")
            fig2.update_yaxes(autorange="reversed")
            st.plotly_chart(style_chart(fig2), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    ch3, ch4 = st.columns(2)

    with ch3:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        c3_head, c3_ctrl = st.columns([2, 1])
        with c3_head:
            st.markdown(f'<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">Regional Distribution</div>', unsafe_allow_html=True)
        with c3_ctrl:
            region_style = st.selectbox("Style", ["Donut", "Vertical Bar", "Pie Chart"], key="ctrl_region", label_visibility="collapsed")

        if region_style == "Vertical Bar":
            fig3 = go.Figure(go.Bar(
                x=region_df[region_col], y=region_df["Revenue"],
                marker_color=PALETTE[:len(region_df)],
                text=[f"{curr_sym}{v:,.0f}" for v in region_df["Revenue"]],
                textposition="outside", textfont=dict(color=TEXT_COLOR, size=10),
            ))
            fig3.update_yaxes(tickprefix=curr_sym, tickformat=",.0f")
            st.plotly_chart(style_chart(fig3), use_container_width=True)
        elif region_style == "Pie Chart":
            fig3 = go.Figure(go.Pie(
                labels=region_df[region_col], values=region_df["Revenue"],
                marker=dict(colors=PALETTE[:len(region_df)], line=dict(color=DARK_BG, width=2)),
                textinfo="label+percent", textfont=dict(color="#F8FAFC", size=11),
            ))
            fig3.update_layout(
                paper_bgcolor=DARK_BG,
                margin=dict(l=20, r=20, t=16, b=20),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_COLOR)),
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            fig3 = go.Figure(go.Pie(
                labels=region_df[region_col], values=region_df["Revenue"],
                hole=0.55,
                marker=dict(colors=PALETTE[:len(region_df)], line=dict(color=DARK_BG, width=2)),
                textinfo="label+percent", textfont=dict(color="#F8FAFC", size=11),
            ))
            fig3.update_layout(
                paper_bgcolor=DARK_BG,
                margin=dict(l=20, r=20, t=16, b=20),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_COLOR)),
            )
            st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch4:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        c4_head, c4_cat, c4_c1, c4_c2 = st.columns([1.5, 1.3, 1.1, 0.7])
        with c4_head:
            st.markdown(f'<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">Product Leaderboard</div>', unsafe_allow_html=True)
        with c4_cat:
            cat_filter_opts = ["All Categories"]
            if cat_col in scoped_df.columns:
                cat_filter_opts += sorted([str(c) for c in scoped_df[cat_col].dropna().unique().tolist()])
            sel_cat = st.selectbox("Category", cat_filter_opts, key="ctrl_prod_cat", label_visibility="collapsed", help="Filter products by category vertical")
        with c4_c1:
            metric_options = ["Revenue", "Profit", "Quantity"] if has_profit else ["Revenue", "Quantity"]
            top_metric = st.selectbox("Metric", metric_options, key="ctrl_metric", label_visibility="collapsed")
        with c4_c2:
            top_n = st.selectbox("Count", [5, 10], key="ctrl_count", label_visibility="collapsed")

        # Aggregate dynamically using scoped_df and category filter
        prod_df_slice = scoped_df
        if sel_cat != "All Categories" and cat_col in prod_df_slice.columns:
            cat_filtered = prod_df_slice[prod_df_slice[cat_col] == sel_cat]
            if not cat_filtered.empty:
                prod_df_slice = cat_filtered

        prod_col_name = "Product" if "Product" in prod_df_slice.columns else ("Category" if "Category" in prod_df_slice.columns else cat_col)

        agg_spec = {
            "Revenue": ("Revenue", "sum"),
            "Quantity": ("Quantity", "sum") if "Quantity" in prod_df_slice.columns else ("Revenue", "count")
        }
        if has_profit and "Profit" in prod_df_slice.columns:
            agg_spec["Profit"] = ("Profit", "sum")
        else:
            agg_spec["Profit"] = ("Revenue", lambda s: 0.0)

        prod_rank = prod_df_slice.groupby(prod_col_name).agg(**agg_spec).reset_index().rename(columns={prod_col_name: "Product"})
        prod_rank = prod_rank.sort_values(top_metric, ascending=False).head(top_n)

        is_curr = top_metric in ["Revenue", "Profit"]
        fig4 = go.Figure(go.Bar(
            x=prod_rank["Product"], y=prod_rank[top_metric],
            marker_color=PALETTE[:len(prod_rank)],
            text=[f"{curr_sym}{v:,.0f}" if is_curr else f"{int(v):,} units" for v in prod_rank[top_metric]],
            textposition="outside", textfont=dict(color=TEXT_COLOR, size=10),
        ))
        if is_curr:
            fig4.update_yaxes(tickprefix=curr_sym, tickformat=",.0f")
        else:
            fig4.update_yaxes(tickformat=",.0f")
        st.plotly_chart(style_chart(fig4, n_bars=len(prod_rank), tickangle=-25), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


    # ─────────────────────────────────────────────────────────────────────────────
    # EXECUTIVE TALKING POINTS
    # ─────────────────────────────────────────────────────────────────────────────
    ai_badge = '<span style="margin-left:12px;font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;background:rgba(99,102,241,0.2);border:1px solid #6366F1;color:#A5B4FC;">✦ AI-Powered by Gemini</span>' if narrative.get("status") == "ai_generated" else ''

    st.markdown(f'<div class="section-title">Automated Executive Takeaways{ai_badge}</div>', unsafe_allow_html=True)

    takeaway_cards_html = "".join([
        f'<div class="insight-card"><div class="insight-title">{h(t.get("icon", "💡"))} {h(t.get("title", "Key Finding"))}</div><div class="insight-body">{h(t.get("body", ""))}</div></div>'
        for t in takeaways[:3]
    ])

    st.markdown(f'<div class="insight-grid">{takeaway_cards_html}</div>', unsafe_allow_html=True)


with tab_deck:
    # ─────────────────────────────────────────────────────────────────────────────
    # SLIDE CAROUSEL PREVIEW (Interactive 16:9 Deck Viewer)
    # ─────────────────────────────────────────────────────────────────────────────
    if "slide_idx" not in st.session_state:
        st.session_state.slide_idx = 0

    margin_str = f"{profit_margin:.1f}%" if profit_margin is not None else "N/A"
    profit_str = fmt(total_profit) if total_profit is not None else "N/A"

    # Brand kit preview integrations
    import base64
    logo_b64 = f"data:image/png;base64,{base64.b64encode(logo_file.getvalue()).decode()}" if ('logo_file' in locals() and logo_file) else None
    logo_img_tag = f'<img src="{logo_b64}" style="max-height:42px;max-width:140px;object-fit:contain;margin-bottom:14px;display:block;" />' if logo_b64 else ''
    accent_tint = brand_color if ('brand_color' in locals() and brand_color) else "#6366F1"

    recs_grid_html = ""
    for r in recs[:4]:
        accent = r.get("accent", accent_tint)
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(accent or "")):
            accent = accent_tint
        recs_grid_html += f'''<div style="background:#111827;border:1px solid #1F2937;border-left:3px solid {accent};border-radius:10px;padding:16px;"><div style="font-size:11px;font-weight:700;color:{accent};text-transform:uppercase;">{h(r.get('tag', ''))}</div><div style="font-size:13px;color:#CBD5E1;margin-top:6px;line-height:1.5;"><strong>{h(r.get('title', ''))}:</strong> {h(r.get('body', ''))}</div></div>'''

    best_period       = insights.get("best_period", best_month)
    worst_period      = insights.get("worst_period", worst_month)
    best_period_tag   = insights.get("best_period_tag", "🏆 Annual High-Water Mark")
    worst_period_tag  = insights.get("worst_period_tag", "⚠️ Contraction Window")
    best_period_desc  = insights.get("best_period_desc", "Highest activity concentration recorded. Driven by aligned campaign flights and peak demand velocity.")
    worst_period_desc = insights.get("worst_period_desc", "Softest period recorded. Represents our primary opportunity for strategic counter-cyclical initiatives.")
    trend_slide_title = insights.get("trend_title") or meta.get("trend_title", "Performance Trajectory & Trend")
    period_guidance   = insights.get("period_guidance", f"Review capacity and planning ahead of best_period, the strongest period in this data.")

    slides = [
        {
            "num": "01",
            "name": "Executive Cover",
            "icon": "🏷️",
            "tag": f"EXECUTIVE BRIEFING · {h(report_mode.upper())}",
            "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:20px 0;">{logo_img_tag}<h1 style="font-size:36px;font-weight:800;color:#F8FAFC;margin:0 0 12px 0;letter-spacing:-0.02em;line-height:1.2;">{h(report_title)}</h1><p style="font-size:15px;color:#94A3B8;margin:0 0 24px 0;line-height:1.6;">Automated Executive Analysis & Strategic Action Plan</p><div style="display:flex;gap:20px;font-size:12px;color:#64748B;"><span style="color:{accent_tint};">● Certified Dataset</span><span>{len(df):,} Validated Records</span><span>Confidential · Boardroom Ready</span></div></div>''',
            "notes": speaker_notes.get("slide_1", f"Welcome everyone. Today we are reviewing our executive performance report for {report_title}. We will walk through our high-level KPIs, seasonal trends, category margin health, and strategic growth priorities.")
        },
        {
            "num": "02",
            "name": "KPI Matrix",
            "icon": "📌",
            "tag": "EXECUTIVE HIGHLIGHTS · SLIDE 02",
            "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:10px 0;"><div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-bottom:18px;">Executive Financial & Operational Summary</div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px;"><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:18px;"><div style="font-size:10px;color:#64748B;font-weight:700;letter-spacing:0.06em;">{h(kpi_rev_lbl.upper())}</div><div style="font-size:26px;font-weight:800;color:#F8FAFC;margin-top:6px;">{fmt(total_revenue)}</div><div style="font-size:11px;color:#38BDF8;margin-top:4px;">{h(insights.get("growth_label") or "Not enough history")}</div></div><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:18px;"><div style="font-size:10px;color:#64748B;font-weight:700;letter-spacing:0.06em;">{h(kpi_profit_lbl.upper())}</div><div style="font-size:26px;font-weight:800;color:#34D399;margin-top:6px;">{profit_str}</div><div style="font-size:11px;color:#34D399;margin-top:4px;">{h(profit_pill)}</div></div><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:18px;"><div style="font-size:10px;color:#64748B;font-weight:700;letter-spacing:0.06em;">{h(kpi_margin_lbl.upper())}</div><div style="font-size:26px;font-weight:800;color:#C084FC;margin-top:6px;">{margin_str}</div><div style="font-size:11px;color:#C084FC;margin-top:4px;">{h(margin_pill)}</div></div><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:18px;"><div style="font-size:10px;color:#64748B;font-weight:700;letter-spacing:0.06em;">{h(kpi_vol_lbl.upper())}</div><div style="font-size:26px;font-weight:800;color:#FBBF24;margin-top:6px;">{total_orders:,}</div><div style="font-size:11px;color:#FBBF24;margin-top:4px;">{h(kpi_aov_lbl)}: {fmt(avg_order_val)}</div></div></div><div style="background:#111827;border:1px solid #1F2937;border-left:3px solid #6366F1;border-radius:8px;padding:12px 16px;font-size:13px;color:#94A3B8;">● Key Takeaway: {h(kpi_rev_lbl)} closed at {fmt(total_revenue)} with {h(kpi_margin_lbl)} at {margin_str}.</div></div>''',
            "notes": speaker_notes.get("slide_2", f"Slide 2 outlines our bottom-line numbers. Net profit reached {profit_str} on {fmt(total_revenue)} of gross revenue. With an average order value of {fmt(avg_order_val)}, our {margin_str} margins give us substantial headroom to invest in marketing.")
        },
        {
            "num": "03",
            "name": "Trajectory",
            "icon": "📈",
            "tag": "MOMENTUM & PACING · SLIDE 03",
            "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:10px 0;"><div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-bottom:14px;">{h(trend_slide_title)}</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px;"><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:20px;"><div style="font-size:11px;color:#38BDF8;font-weight:700;text-transform:uppercase;">{h(best_period_tag)}</div><div style="font-size:24px;font-weight:800;color:#F8FAFC;margin:8px 0 4px 0;">{h(best_period)}</div><p style="font-size:13px;color:#94A3B8;margin:0;line-height:1.5;">{h(best_period_desc)}</p></div><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:20px;"><div style="font-size:11px;color:#F87171;font-weight:700;text-transform:uppercase;">{h(worst_period_tag)}</div><div style="font-size:24px;font-weight:800;color:#F8FAFC;margin:8px 0 4px 0;">{h(worst_period)}</div><p style="font-size:13px;color:#94A3B8;margin:0;line-height:1.5;">{h(worst_period_desc)}</p></div></div><div style="background:#111827;border:1px solid #1F2937;border-left:3px solid #38BDF8;border-radius:8px;padding:12px 16px;font-size:13px;color:#94A3B8;">● Executive Guidance: {h(period_guidance)}</div></div>''',
            "notes": speaker_notes.get("slide_3", f"Slide 3 outlines our performance trajectory. Peak delivery occurred in {best_period}, while {worst_period} represented our lowest volume period. {period_guidance}")
        },
        {
            "num": "04",
            "name": "Segmentation",
            "icon": "🏆",
            "tag": "PORTFOLIO MIX · SLIDE 04",
            "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:10px 0;"><div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-bottom:14px;">{h(meta.get("category_title", "Portfolio Category & Contribution"))}</div><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:20px;margin-bottom:16px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;"><span style="font-size:16px;font-weight:800;color:#F8FAFC;">Top Vertical: {h(top_cat)}</span><span style="font-size:12px;font-weight:700;color:#34D399;background:rgba(16,185,129,0.12);padding:4px 10px;border-radius:12px;">{margin_str} Efficiency Index</span></div><p style="font-size:13px;color:#94A3B8;margin:0;line-height:1.6;">{h(top_cat)} accounts for the single largest volume and return contribution in our portfolio. Velocity is supported by high organic repeat rates.</p></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;"><div style="background:#111827;border:1px solid #1F2937;border-left:3px solid #C084FC;border-radius:8px;padding:12px 16px;font-size:12px;color:#94A3B8;"><strong style="color:#F8FAFC;">Lead Driver Focus:</strong> Double down on top 5 performing units to capture compounding scale.</div><div style="background:#111827;border:1px solid #1F2937;border-left:3px solid #FBBF24;border-radius:8px;padding:12px 16px;font-size:12px;color:#94A3B8;"><strong style="color:#F8FAFC;">Efficiency Expansion:</strong> Audit lower-velocity categories on the cost side to optimize margin.</div></div></div>''',
            "notes": speaker_notes.get("slide_4", f"On slide 4, {top_cat} is our clear anchor category. It produces the bulk of our gross margin. Our recommendation here is to double down on inventory depth for our top 5 SKUs while reviewing cost structures for trailing categories.")
        },
        {
            "num": "05",
            "name": "Action Plan",
            "icon": "📍",
            "tag": "STRATEGIC ROADMAP · SLIDE 05",
            "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:10px 0;"><div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-bottom:14px;">{h(meta.get("region_title", "Strategic Priorities & Next Steps"))}</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;">{recs_grid_html}</div></div>''',
            "notes": speaker_notes.get("slide_5", f"Finally, slide 5 gives leadership four immediate action items: First, capture more market share in {top_region}; second, protect our {margin_str} margins; third, launch campaigns to lift {worst_period}; and fourth, test bundle add-ons to increase our {fmt(avg_order_val)} average order value.")
        },
    ]

    render_slide_carousel(slides)

    # ─────────────────────────────────────────────────────────────────────────────
    # POWERPOINT EXPORT PIPELINE (On-Demand & Cached for Instant Carousel Transitions)
    # ─────────────────────────────────────────────────────────────────────────────
    if "pptx_cache" not in st.session_state:
        st.session_state.pptx_cache = {}

    active_trend  = st.session_state.get("ctrl_trend", trend_style)
    active_cat    = st.session_state.get("ctrl_cat", cat_style)
    active_region = st.session_state.get("ctrl_region", region_style)
    active_metric = st.session_state.get("ctrl_metric", top_metric)
    active_top_n  = st.session_state.get("ctrl_count", top_n)

    logo_name = logo_file.name if ('logo_file' in locals() and logo_file) else None
    bc_val = brand_color if 'brand_color' in locals() else None
    bn_val = brand_name if 'brand_name' in locals() else None
    active_prod_cat   = st.session_state.get("ctrl_prod_cat", "All Categories")
    active_drill_year = st.session_state.get("drill_year", "All")
    active_drill_gran = st.session_state.get("drill_gran", "Monthly")
    pptx_cache_key = (
        data_hash,
        active_scope_id,
        active_prod_cat,
        active_trend,
        active_cat,
        active_region,
        active_metric,
        active_top_n,
        active_drill_year,
        active_drill_gran,
        bc_val,
        bn_val,
        logo_name,
        report_title,
        report_mode,
        curr_sym,
    )

    export_report_title = f"{report_title} ({active_scope_name})" if active_scope_id != "all" else report_title
    safe_title = export_report_title.replace(" ", "_")

    if pptx_cache_key in st.session_state.pptx_cache:
        col_dl, col_rebuild = st.columns([3, 1])
        with col_dl:
            st.download_button(
                label="📥  Download Executive PowerPoint Deck (.pptx)",
                data=st.session_state.pptx_cache[pptx_cache_key],
                file_name=f"{safe_title}.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
                type="primary",
            )
        with col_rebuild:
            if st.button("🔄 Recompile", use_container_width=True, help="Re-render charts and rebuild presentation"):
                del st.session_state.pptx_cache[pptx_cache_key]
                st.rerun()
    else:
        if st.button("🚀  Generate Executive PowerPoint Deck (.pptx)", type="primary", use_container_width=True):
            with st.spinner("🎨 Rendering high-resolution chart PNGs and compiling PowerPoint deck..."):
                import tempfile
                import chart_engine
                from chart_engine   import generate_all_charts
                from slide_builder  import build_presentation

                # Synchronize ranking and aggregation dynamically with active metric, count, and category filter
                prod_df_slice = scoped_df
                if active_prod_cat != "All Categories" and cat_col in prod_df_slice.columns:
                    cat_filtered = prod_df_slice[prod_df_slice[cat_col] == active_prod_cat]
                    if not cat_filtered.empty:
                        prod_df_slice = cat_filtered

                prod_col_name = "Product" if "Product" in prod_df_slice.columns else ("Category" if "Category" in prod_df_slice.columns else cat_col)
                agg_spec = {
                    "Revenue": ("Revenue", "sum"),
                    "Quantity": ("Quantity", "sum") if "Quantity" in prod_df_slice.columns else ("Revenue", "count")
                }
                if has_profit and "Profit" in prod_df_slice.columns:
                    agg_spec["Profit"] = ("Profit", "sum")
                else:
                    agg_spec["Profit"] = ("Revenue", lambda s: 0.0)

                sync_rank = prod_df_slice.groupby(prod_col_name).agg(**agg_spec).reset_index().rename(columns={prod_col_name: "Product"})
                sync_rank = sync_rank.sort_values(active_metric, ascending=False).head(active_top_n)

                # Assemble presentation report data with active scope and filters
                presentation_report = dict(view_report)
                presentation_report["df"] = scoped_df
                presentation_report["kpis"] = kpis
                presentation_report["category"] = category
                presentation_report["region"] = region_df
                presentation_report["top_products"] = sync_rank

                chart_config = {
                    "trend_type":  active_trend,
                    "cat_type":    active_cat,
                    "region_type": active_region,
                    "top_metric":  active_metric,
                    "brand_color": bc_val,
                }

                # Isolated temporary directory ensures simultaneous users never overwrite each other's charts/decks
                with tempfile.TemporaryDirectory() as tmp_dir:
                    logo_path = None
                    if 'logo_file' in locals() and logo_file:
                        logo_ext = logo_file.name.split('.')[-1]
                        logo_path = os.path.join(tmp_dir, f"brand_logo.{logo_ext}")
                        with open(logo_path, "wb") as f:
                            f.write(logo_file.getbuffer())

                    try:
                        chart_paths = generate_all_charts(presentation_report, config=chart_config, output_dir=tmp_dir)
                    except chart_engine.ChartExportError as chart_err:
                        st.error(f"⚠️ The deck was NOT built because a chart image could not be rendered. {chart_err}")
                        st.stop()

                    pptx_path   = build_presentation(
                        presentation_report, chart_paths,
                        report_title=export_report_title,
                        narrative=narrative,
                        output_dir=tmp_dir,
                        brand_color=bc_val,
                        logo_path=logo_path,
                        brand_name=bn_val,
                    )
                    with open(pptx_path, "rb") as f:
                        pptx_bytes = f.read()

                st.session_state.pptx_cache[pptx_cache_key] = pptx_bytes
                st.rerun()

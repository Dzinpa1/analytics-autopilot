"""
app.py  —  Analytics AutoPilot
Design System: Linear Obsidian (Dark Pro Studio)
Run with:  python -m streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os, io
import plotly.graph_objects as go

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
html, body, [data-testid="stAppViewContainer"], .stApp {
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
        <div class="ap-badge">Linear Obsidian</div>
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
    <div class="hero-desc">
        Drop any CSV or Excel file. AutoPilot computes statistical KPIs, generates branded high-density charts,
        extracts strategic talking points, and compiles a downloadable 5-slide PowerPoint deck instantly.
    </div>
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
        ["Sales & Retail Performance", "Marketing & Ad Campaign ROI", "Operations & Expense Tracker"],
        index=0,
        label_visibility="collapsed",
        help="Adapts KPI metrics, AI boardroom commentary, and slide structures to your specific business workflow."
    )

    default_titles = {
        "Sales & Retail Performance": "2024 Sales Performance Review",
        "Marketing & Ad Campaign ROI": "2024 Marketing ROI & Ad Spend Review",
        "Operations & Expense Tracker": "2024 Operations & Expense Report"
    }

    # 2. Presentation Title
    st.markdown('<div style="font-size:11px;font-weight:700;color:#818CF8;text-transform:uppercase;letter-spacing:0.06em;margin-top:14px;margin-bottom:6px;">2. Presentation Title</div>', unsafe_allow_html=True)
    suggested_title = default_titles.get(report_mode, "2024 Executive Performance Review")
    report_title = st.text_input("Presentation Title", value=suggested_title, label_visibility="collapsed")

    # 3. Data Source
    st.markdown('<div style="font-size:11px;font-weight:700;color:#818CF8;text-transform:uppercase;letter-spacing:0.06em;margin-top:14px;margin-bottom:6px;">3. Data Source (.csv, .xlsx)</div>', unsafe_allow_html=True)
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
    use_sample = st.checkbox("⚡ Load sample dataset", value=False if uploaded_file else True)

if not uploaded_file and not use_sample:
    st.info("👈 **Welcome to AutoPilot Studio!**\n\nPlease upload a dataset (.csv or .xlsx) or check **'Load sample dataset'** in the sidebar to generate your executive report.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# LOAD & PREPARE DATA
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("Processing data engine..."):
    if use_sample or uploaded_file is None:
        from generate_data import generate_sales_data
        df = generate_sales_data()
    else:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

cols = df.columns.tolist()
def fcol(candidates):
    for c in candidates:
        for col in cols:
            if c.lower() in col.lower(): return col
    return cols[0]

def fcol_opt(candidates):
    for c in candidates:
        for col in cols:
            if c.lower() in col.lower(): return col
    return "None / Not Available"

# Mode-specific column candidate prioritization
if "Marketing" in report_mode:
    date_col    = fcol(["date","time","day","month","period"])
    revenue_col = fcol(["spend","ad_spend","budget","investment","revenue","sales","cost","amount","total"])
    profit_col  = fcol_opt(["conversions","leads","acquisitions","return","profit","margin","net"])
    cost_col    = fcol_opt(["cpc","cpa","cost","expense"])
    cat_col     = fcol_opt(["channel","campaign","network","source","medium","category","type"])
    region_col  = fcol_opt(["region","country","market","geo","location","city","audience"])
elif "Operations" in report_mode:
    date_col    = fcol(["date","time","day","month","period"])
    revenue_col = fcol(["budget","allocated","target","total_budget","revenue","amount","total"])
    profit_col  = fcol_opt(["expense","actual","spend","cost","variance","profit"])
    cost_col    = fcol_opt(["cogs","fixed_cost","variable_cost","overhead","cost"])
    cat_col     = fcol_opt(["department","dept","cost_center","unit","function","category","type"])
    region_col  = fcol_opt(["facility","branch","site","warehouse","region","location","plant"])
else:  # Sales & Retail Performance
    date_col    = fcol(["date","time","day","month"])
    revenue_col = fcol(["revenue","sales","amount","income","total"])
    profit_col  = fcol_opt(["profit","margin","net"])
    cost_col    = fcol_opt(["cost","expense","cogs"])
    cat_col     = fcol_opt(["category","type","segment"])
    region_col  = fcol_opt(["region","area","zone","location"])

opt_cols = ["None / Not Available"] + cols

# Sidebar Expanders for advanced workspace settings
with st.sidebar:
    with st.expander("⚙️ Verify Auto-Mapped Columns", expanded=False):
        rev_input_label = "Spend / Revenue" if "Marketing" in report_mode else ("Budget / Allocation" if "Operations" in report_mode else "Revenue Column")
        date_col    = st.selectbox("Date Column", cols, index=cols.index(date_col))
        revenue_col = st.selectbox(rev_input_label, cols, index=cols.index(revenue_col))
        profit_input_label = "Conversions / Return" if "Marketing" in report_mode else ("Actual Expenses" if "Operations" in report_mode else "Profit Column")
        profit_col  = st.selectbox(profit_input_label, opt_cols, index=opt_cols.index(profit_col))
        cost_col    = st.selectbox("Cost / CPA Column", opt_cols, index=opt_cols.index(cost_col))
        cat_input_label = "Channel / Campaign" if "Marketing" in report_mode else ("Department / Unit" if "Operations" in report_mode else "Category Column")
        reg_input_label = "Market / Geo" if "Marketing" in report_mode else ("Facility / Location" if "Operations" in report_mode else "Region Column")
        cat_col     = st.selectbox(cat_input_label, opt_cols, index=opt_cols.index(cat_col))
        region_col  = st.selectbox(reg_input_label, opt_cols, index=opt_cols.index(region_col))

    with st.expander("🤖 AI Intelligence (Gemini)", expanded=False):
        gemini_api_key_input = st.text_input(
            "Gemini API Key (Optional)",
            type="password",
            placeholder="AIzaSy... (leave blank for template)",
            help="Paste your Gemini API key to generate live tailored executive narratives and speaker scripts. Key is stored only in session state."
        )
        if not gemini_api_key_input:
            st.caption(f"✦ Using built-in deterministic {report_mode} executive commentary.")

    with st.expander("🎨 Brand Kit & White-Labeling", expanded=False):
        currency_options = ["$", "₵", "₦", "£", "€", "None"]
        currency_symbol = st.selectbox("Currency Symbol", currency_options, index=0, help="Currency symbol used across KPI cards, chart axes, and presentation slides.")
        curr_sym = "" if currency_symbol == "None" else currency_symbol
        brand_color = st.color_picker("Brand Accent Color", value="#6366F1", help="Select corporate accent color to theme the PowerPoint presentation.")
        logo_file = st.file_uploader("Brand Logo (.png, .jpg)", type=["png", "jpg", "jpeg"], help="Optional: Upload company logo for slide headers and cover.")

# ─────────────────────────────────────────────────────────────────────────────
# COMPUTE METRICS VIA ANALYSIS ENGINE (Single Source of Truth, Cached)
# ─────────────────────────────────────────────────────────────────────────────
from analysis_engine import build_report_from_df

col_mapping = {
    "date": date_col,
    "revenue": revenue_col,
    "profit": profit_col if profit_col != "None / Not Available" else None,
    "cost": cost_col if cost_col != "None / Not Available" else None,
    "category": cat_col if cat_col != "None / Not Available" else None,
    "region": region_col if region_col != "None / Not Available" else None,
    "product": "Product" if "Product" in df.columns else (cat_col if cat_col != "None / Not Available" else None),
}

@st.cache_data(show_spinner=False)
def get_cached_report(_df, mapping, mode, curr):
    return build_report_from_df(_df, mapping=mapping, report_mode=mode, currency_symbol=curr)

try:
    report_data = get_cached_report(df, col_mapping, report_mode, curr_sym)
except Exception as e:
    st.error(f"⚠️ **Could not process this spreadsheet:** {str(e)}\n\nPlease ensure your Date and Revenue columns contain valid values.")
    st.stop()

kpis      = report_data["kpis"]
monthly   = report_data["monthly"]
category  = report_data["category"]
region_df = report_data["region"]
insights  = report_data["insights"]
hygiene   = report_data.get("hygiene", {})

# Render Data Hygiene Audit Log in Sidebar
with st.sidebar:
    with st.expander("🛡️ Data Hygiene & Audit Trail", expanded=False):
        score = hygiene.get('health_score', 100)
        status = hygiene.get('health_status', 'Certified Clean')
        status_color = "#34D399" if score >= 98 else "#FBBF24"
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
            <span style="font-size:11px;font-weight:700;color:#94A3B8;text-transform:uppercase;">Data Integrity</span>
            <span style="font-size:11px;font-weight:700;color:{status_color};background:rgba(16,185,129,0.12);padding:2px 8px;border-radius:10px;border:1px solid rgba(16,185,129,0.25);">✦ {status} ({score}%)</span>
        </div>
        <div style="font-size:12px;color:#CBD5E1;line-height:1.6;margin-bottom:10px;">
            <div>• <strong>{hygiene.get('clean_row_count', 0):,}</strong> records parsed (100% retention)</div>
            <div>• Coverage: <strong>{hygiene.get('date_range', 'Validated')}</strong></div>
            <div>• Sanitized formatters/nulls: <strong>{hygiene.get('currency_symbols_stripped', 0) + hygiene.get('missing_values_imputed', 0):,}</strong></div>
        </div>
        """, unsafe_allow_html=True)
        if hygiene.get("audit_log"):
            st.markdown('<div style="font-size:11px;font-weight:700;color:#818CF8;margin-bottom:6px;text-transform:uppercase;">Automated Audit Trail:</div>', unsafe_allow_html=True)
            for step in hygiene["audit_log"]:
                st.markdown(f'<div style="font-size:11px;color:#94A3B8;margin-bottom:3px;">✔ {step}</div>', unsafe_allow_html=True)

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
mom_avg     = insights["avg_mom_growth"]
cat_col     = "Category"
region_col  = "Region"
meta        = report_data.get("meta", {})

def fmt(v):
    if v is None: return "N/A"
    prefix = curr_sym
    if v >= 1_000_000: return f"{prefix}{v/1_000_000:.2f}M"
    elif v >= 1_000:   return f"{prefix}{v/1_000:.1f}K"
    return f"{prefix}{v:,.0f}"

profit_display = fmt(total_profit) if has_profit and total_profit is not None else "Not Available"
profit_pill    = meta.get("profit_sub", "After All Costs") if has_profit and total_profit is not None else "Allocation Mode"

if has_profit and profit_margin is not None:
    margin_display = f"{profit_margin:.1f}%"
    margin_pill    = "Target: >35.0%" if profit_margin >= 35.0 else "Below 35% Target"
    margin_pill_class = "pill-purple" if profit_margin >= 35.0 else "pill-amber"
else:
    margin_display = "N/A"
    margin_pill    = "Margin Unmapped"
    margin_pill_class = "pill-blue"

# ─────────────────────────────────────────────────────────────────────────────
# AI NARRATIVE GENERATION (Cached in st.session_state)
# ─────────────────────────────────────────────────────────────────────────────
from ai_narrator import generate_narrative, get_gemini_api_key

active_api_key = (gemini_api_key_input.strip() if 'gemini_api_key_input' in locals() and gemini_api_key_input else None) or get_gemini_api_key()

cache_key = f"nar_{report_mode}_{report_title}_{total_revenue}_{total_orders}_{curr_sym}_{bool(active_api_key)}"
if "narrative_cache" not in st.session_state:
    st.session_state.narrative_cache = {}

if cache_key not in st.session_state.narrative_cache:
    with st.spinner(f"🧠 Synthesizing executive narrative ({report_mode})..."):
        st.session_state.narrative_cache[cache_key] = generate_narrative(
            report_data, report_title=report_title, report_mode=report_mode, api_key=active_api_key
        )

narrative     = st.session_state.narrative_cache[cache_key]
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

tab_dash, tab_deck = st.tabs(["📊 Executive Dashboard", "🖥️ Slide Deck Preview & Export"])

with tab_dash:
    # ─────────────────────────────────────────────────────────────────────────────
    # KPI CARDS (Linear Obsidian Style)
    # ─────────────────────────────────────────────────────────────────────────────
    hygiene_pill = f'<span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:10px;background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.25);color:#34D399;margin-left:8px;">✔ {hygiene.get("clean_row_count", len(df)):,} Records Certified</span>'
    st.markdown(f'<div class="section-title">Core Performance Indicators <span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:10px;background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);color:#A5B4FC;margin-left:8px;">{report_mode}</span>{hygiene_pill}</div>', unsafe_allow_html=True)

    if narrative.get("executive_summary"):
        anomalies = insights.get("anomalies", [])
        anom_badge = ""
        if anomalies:
            top_a = anomalies[0]
            anom_color = "#34D399" if top_a["type"] == "Surge" else "#F87171"
            anom_bg = "rgba(16, 185, 129, 0.12)" if top_a["type"] == "Surge" else "rgba(248, 113, 113, 0.12)"
            anom_border = "rgba(16, 185, 129, 0.3)" if top_a["type"] == "Surge" else "rgba(248, 113, 113, 0.3)"
            anom_badge = (
                f'<div style="margin-top:12px;padding:8px 14px;border-radius:8px;background:{anom_bg};border:1px solid {anom_border};font-size:12px;color:#F8FAFC;display:inline-flex;align-items:center;gap:6px;">'
                f'<span style="font-weight:700;color:{anom_color};">⚡ STATISTICAL {top_a["type"].upper()} DETECTED:</span>'
                f'{top_a["period"]} recorded {top_a["pct_diff_mean"]:+.1f}% vs. baseline ({top_a["z_score"]:+.2f}σ deviation)'
                f'</div>'
            )

        briefing_html = (
            f'<div style="background:linear-gradient(135deg, rgba(99,102,241,0.08), rgba(56,189,248,0.04));border:1px solid rgba(99,102,241,0.25);border-radius:10px;padding:14px 18px;margin-bottom:20px;font-size:13px;color:#E2E8F0;line-height:1.6;">'
            f'<div><span style="font-weight:700;color:#A5B4FC;margin-right:8px;">✦ EXECUTIVE BRIEFING:</span>{narrative["executive_summary"]}</div>'
            f'{anom_badge}'
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
            <div class="kpi-pill pill-blue">↑ {mom_avg:.1f}% Avg MoM</div>
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
    st.markdown('<div class="section-title">Interactive Analytics Engine · Customizable Visuals</div>', unsafe_allow_html=True)

    DARK_BG    = "#111827"
    GRID_COLOR = "#1F2937"
    TEXT_COLOR = "#94A3B8"
    PALETTE    = ["#6366F1", "#38BDF8", "#818CF8", "#0EA5E9", "#A5B4FC", "#64748B"]

    def style_chart(fig, title):
        fig.update_layout(
            paper_bgcolor=DARK_BG,
            plot_bgcolor=DARK_BG,
            font=dict(family="Plus Jakarta Sans", color=TEXT_COLOR),
            title=dict(text=title, font=dict(size=14, color="#F8FAFC", family="Plus Jakarta Sans"), x=0.03),
            margin=dict(l=48, r=24, t=54, b=40),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_COLOR)),
        )
        fig.update_xaxes(showgrid=False, linecolor=GRID_COLOR, tickcolor=GRID_COLOR)
        fig.update_yaxes(showgrid=True, gridcolor=GRID_COLOR, linecolor=GRID_COLOR)
        return fig

    import plotly.express as px

    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        c1_head, c1_ctrl = st.columns([2, 1])
        with c1_head:
            anom_pill = f'<span style="font-size:10px;font-weight:700;color:#FBBF24;background:rgba(245,158,11,0.15);padding:2px 7px;border-radius:10px;border:1px solid rgba(245,158,11,0.3);margin-left:6px;">⚡ {len(anomalies)} Outlier{"s" if len(anomalies) > 1 else ""}</span>' if anomalies else ""
            st.markdown(f'<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">Monthly Performance{anom_pill}</div>', unsafe_allow_html=True)
        with c1_ctrl:
            trend_style = st.selectbox("Style", ["Grouped Bars", "Line & Area", "MoM Growth %"], key="ctrl_trend", label_visibility="collapsed")

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
                chart1_title = "Revenue & Profit Trajectory (Line)"
            else:
                chart1_title = "Monthly Revenue Trajectory (Line)"
            fig1.update_yaxes(tickprefix=curr_sym, tickformat=",.0f")
            st.plotly_chart(style_chart(fig1, chart1_title), use_container_width=True)
        elif trend_style == "MoM Growth %":
            growth_colors = ["#34D399" if v >= 0 else "#F87171" for v in monthly["MoM_Growth"].fillna(0)]
            fig1.add_trace(go.Bar(
                x=monthly["Month_Label"], y=monthly["MoM_Growth"],
                marker_color=growth_colors,
                text=[f"{v:+.1f}%" if not pd.isna(v) else "0.0%" for v in monthly["MoM_Growth"]],
                textposition="outside", textfont=dict(color=TEXT_COLOR, size=10),
            ))
            fig1.update_yaxes(ticksuffix="%")
            st.plotly_chart(style_chart(fig1, "Month-over-Month Velocity (%)"), use_container_width=True)
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
                chart1_title = "Monthly Revenue vs Net Profit"
            else:
                chart1_title = "Monthly Revenue Performance"
            fig1.update_yaxes(tickprefix=curr_sym, tickformat=",.0f")
            st.plotly_chart(style_chart(fig1, chart1_title), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        c2_head, c2_ctrl = st.columns([2, 1])
        with c2_head:
            st.markdown(f'<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">Category Portfolio</div>', unsafe_allow_html=True)
        with c2_ctrl:
            cat_style = st.selectbox("Style", ["Horizontal Bar", "Treemap", "Donut"], key="ctrl_cat", label_visibility="collapsed")

        if cat_style == "Treemap":
            color_col = "Margin_%" if has_profit else "Revenue"
            treemap_title = f"{cat_col} Revenue Distribution & Margin %" if has_profit else f"{cat_col} Revenue Distribution"
            fig2 = px.treemap(
                category, path=[cat_col], values="Revenue",
                color=color_col, color_continuous_scale=["#1E1B4B", "#312E81", "#4F46E5", "#38BDF8"],
                title=treemap_title
            )
            fig2.update_layout(
                paper_bgcolor=DARK_BG, plot_bgcolor=DARK_BG,
                font=dict(family="Plus Jakarta Sans", color=TEXT_COLOR),
                margin=dict(l=20, r=20, t=50, b=20),
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
                title=dict(text=f"Revenue Share by {cat_col}", font=dict(size=14, color="#F8FAFC"), x=0.03),
                margin=dict(l=20, r=20, t=50, b=20),
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
            bar_title = f"Revenue & Margin by {cat_col}" if has_profit else f"Revenue by {cat_col}"
            st.plotly_chart(style_chart(fig2, bar_title), use_container_width=True)
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
            st.plotly_chart(style_chart(fig3, f"Revenue by {region_col}"), use_container_width=True)
        elif region_style == "Pie Chart":
            fig3 = go.Figure(go.Pie(
                labels=region_df[region_col], values=region_df["Revenue"],
                marker=dict(colors=PALETTE[:len(region_df)], line=dict(color=DARK_BG, width=2)),
                textinfo="label+percent", textfont=dict(color="#F8FAFC", size=11),
            ))
            fig3.update_layout(
                paper_bgcolor=DARK_BG,
                title=dict(text=f"Market Share by {region_col}", font=dict(size=14, color="#F8FAFC"), x=0.03),
                margin=dict(l=20, r=20, t=54, b=20),
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
                title=dict(text=f"Market Distribution by {region_col}", font=dict(size=14, color="#F8FAFC"), x=0.03),
                margin=dict(l=20, r=20, t=54, b=20),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_COLOR)),
            )
            st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch4:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        c4_head, c4_c1, c4_c2 = st.columns([2, 1, 1])
        with c4_head:
            st.markdown(f'<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">Product Leaderboard</div>', unsafe_allow_html=True)
        with c4_c1:
            metric_options = ["Revenue", "Profit", "Quantity"] if has_profit else ["Revenue", "Quantity"]
            top_metric = st.selectbox("Metric", metric_options, key="ctrl_metric", label_visibility="collapsed")
        with c4_c2:
            top_n = st.selectbox("Count", [5, 10], key="ctrl_count", label_visibility="collapsed")

        # Aggregate dynamically using normalized clean_df
        clean_df = report_data.get("df", df)
        prod_col_name = "Product" if "Product" in clean_df.columns else ("Category" if "Category" in clean_df.columns else cat_col)

        agg_spec = {
            "Revenue": ("Revenue", "sum"),
            "Quantity": ("Quantity", "sum") if "Quantity" in clean_df.columns else ("Revenue", "count")
        }
        if has_profit and "Profit" in clean_df.columns:
            agg_spec["Profit"] = ("Profit", "sum")
        else:
            agg_spec["Profit"] = ("Revenue", lambda s: 0.0)

        prod_rank = clean_df.groupby(prod_col_name).agg(**agg_spec).reset_index().rename(columns={prod_col_name: "Product"})
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
        st.plotly_chart(style_chart(fig4, f"Top {top_n} Products by {top_metric}"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


    # ─────────────────────────────────────────────────────────────────────────────
    # EXECUTIVE TALKING POINTS
    # ─────────────────────────────────────────────────────────────────────────────
    ai_badge = '<span style="margin-left:12px;font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;background:rgba(99,102,241,0.2);border:1px solid #6366F1;color:#A5B4FC;">✦ AI-Powered by Gemini</span>' if narrative.get("status") == "ai_generated" else '<span style="margin-left:12px;font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#94A3B8;">✦ Built-In Analysis</span>'

    st.markdown(f'<div class="section-title">Automated Executive Takeaways {ai_badge}</div>', unsafe_allow_html=True)

    takeaway_cards_html = "".join([
        f'<div class="insight-card"><div class="insight-title">{t.get("icon", "💡")} {t.get("title", "Key Finding")}</div><div class="insight-body">{t.get("body", "")}</div></div>'
        for t in takeaways[:3]
    ])

    st.markdown(f'<div class="insight-grid">{takeaway_cards_html}</div>', unsafe_allow_html=True)


with tab_deck:
    # ─────────────────────────────────────────────────────────────────────────────
    # SLIDE CAROUSEL PREVIEW (Interactive 16:9 Deck Viewer)
    # ─────────────────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Presentation Deck Preview (16:9 Widescreen)</div>', unsafe_allow_html=True)

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
        recs_grid_html += f'''<div style="background:#111827;border:1px solid #1F2937;border-left:3px solid {accent};border-radius:10px;padding:16px;"><div style="font-size:11px;font-weight:700;color:{accent};text-transform:uppercase;">{r.get('tag', '')}</div><div style="font-size:13px;color:#CBD5E1;margin-top:6px;line-height:1.5;"><strong>{r.get('title', '')}:</strong> {r.get('body', '')}</div></div>'''

    slides = [
        {
            "num": "01",
            "name": "Executive Cover",
            "icon": "🏷️",
            "tag": f"EXECUTIVE BRIEFING · {report_mode.upper()}",
            "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:20px 0;">{logo_img_tag}<div style="display:inline-block;padding:4px 12px;border-radius:20px;background:rgba(99,102,241,0.15);border:1px solid {accent_tint};color:#A5B4FC;font-size:11px;font-weight:700;letter-spacing:0.08em;margin-bottom:16px;width:fit-content;">✦ EXECUTIVE REPORT · {report_mode.upper()}</div><h1 style="font-size:36px;font-weight:800;color:#F8FAFC;margin:0 0 12px 0;letter-spacing:-0.02em;line-height:1.2;">{report_title}</h1><p style="font-size:15px;color:#94A3B8;margin:0 0 24px 0;line-height:1.6;">Automated Executive Analysis & Strategic Action Plan</p><div style="display:flex;gap:20px;font-size:12px;color:#64748B;"><span style="color:{accent_tint};">● Certified Dataset</span><span>{len(df):,} Validated Records</span><span>Confidential · Boardroom Ready</span></div></div>''',
            "notes": speaker_notes.get("slide_1", f"Welcome everyone. Today we are reviewing our executive performance report for {report_title}. We will walk through our high-level KPIs, seasonal trends, category margin health, and strategic growth priorities.")
        },
        {
            "num": "02",
            "name": "KPI Matrix",
            "icon": "📌",
            "tag": "EXECUTIVE HIGHLIGHTS · SLIDE 02",
            "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:10px 0;"><div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-bottom:18px;">Executive Financial & Operational Summary</div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px;"><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:18px;"><div style="font-size:10px;color:#64748B;font-weight:700;letter-spacing:0.06em;">{kpi_rev_lbl.upper()}</div><div style="font-size:26px;font-weight:800;color:#F8FAFC;margin-top:6px;">{fmt(total_revenue)}</div><div style="font-size:11px;color:#38BDF8;margin-top:4px;">↑ {mom_avg:.1f}% Avg MoM</div></div><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:18px;"><div style="font-size:10px;color:#64748B;font-weight:700;letter-spacing:0.06em;">{kpi_profit_lbl.upper()}</div><div style="font-size:26px;font-weight:800;color:#34D399;margin-top:6px;">{profit_str}</div><div style="font-size:11px;color:#34D399;margin-top:4px;">{profit_pill}</div></div><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:18px;"><div style="font-size:10px;color:#64748B;font-weight:700;letter-spacing:0.06em;">{kpi_margin_lbl.upper()}</div><div style="font-size:26px;font-weight:800;color:#C084FC;margin-top:6px;">{margin_str}</div><div style="font-size:11px;color:#C084FC;margin-top:4px;">{margin_pill}</div></div><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:18px;"><div style="font-size:10px;color:#64748B;font-weight:700;letter-spacing:0.06em;">{kpi_vol_lbl.upper()}</div><div style="font-size:26px;font-weight:800;color:#FBBF24;margin-top:6px;">{total_orders:,}</div><div style="font-size:11px;color:#FBBF24;margin-top:4px;">{kpi_aov_lbl}: {fmt(avg_order_val)}</div></div></div><div style="background:#111827;border:1px solid #1F2937;border-left:3px solid #6366F1;border-radius:8px;padding:12px 16px;font-size:13px;color:#94A3B8;">● Key Takeaway: {kpi_rev_lbl} closed at {fmt(total_revenue)} with healthy margin retention at {margin_str}, indicating disciplined capital allocation and commercial control.</div></div>''',
            "notes": speaker_notes.get("slide_2", f"Slide 2 outlines our bottom-line numbers. Net profit reached {profit_str} on {fmt(total_revenue)} of gross revenue. With an average order value of {fmt(avg_order_val)}, our {margin_str} margins give us substantial headroom to invest in marketing.")
        },
        {
            "num": "03",
            "name": "Trajectory",
            "icon": "📈",
            "tag": "MOMENTUM & SEASONALITY · SLIDE 03",
            "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:10px 0;"><div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-bottom:14px;">{meta.get("trend_title", "Annual Trajectory & Peak Analysis")}</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px;"><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:20px;"><div style="font-size:11px;color:#38BDF8;font-weight:700;text-transform:uppercase;">🏆 Annual High-Water Mark</div><div style="font-size:24px;font-weight:800;color:#F8FAFC;margin:8px 0 4px 0;">{best_month}</div><p style="font-size:13px;color:#94A3B8;margin:0;line-height:1.5;">Highest activity concentration recorded. Driven by aligned campaign flights and peak demand velocity.</p></div><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:20px;"><div style="font-size:11px;color:#F87171;font-weight:700;text-transform:uppercase;">⚠️ Contraction Window</div><div style="font-size:24px;font-weight:800;color:#F8FAFC;margin:8px 0 4px 0;">{worst_month}</div><p style="font-size:13px;color:#94A3B8;margin:0;line-height:1.5;">Softest period recorded. Represents our primary opportunity for strategic counter-cyclical initiatives.</p></div></div><div style="background:#111827;border:1px solid #1F2937;border-left:3px solid #38BDF8;border-radius:8px;padding:12px 16px;font-size:13px;color:#94A3B8;">● Executive Guidance: Ramp up operational readiness 45 days prior to {best_month} to maximize capture rate.</div></div>''',
            "notes": speaker_notes.get("slide_3", f"Looking at seasonality on slide 3: our peak performance hit in {best_month}. Conversely, {worst_month} showed our seasonal trough. We recommend timing next year's promotional budget to hedge this exact slow period.")
        },
        {
            "num": "04",
            "name": "Segmentation",
            "icon": "🏆",
            "tag": "PORTFOLIO MIX · SLIDE 04",
            "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:10px 0;"><div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-bottom:14px;">{meta.get("category_title", "Portfolio Category & Contribution")}</div><div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:20px;margin-bottom:16px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;"><span style="font-size:16px;font-weight:800;color:#F8FAFC;">Top Vertical: {top_cat}</span><span style="font-size:12px;font-weight:700;color:#34D399;background:rgba(16,185,129,0.12);padding:4px 10px;border-radius:12px;">{margin_str} Efficiency Index</span></div><p style="font-size:13px;color:#94A3B8;margin:0;line-height:1.6;">{top_cat} accounts for the single largest volume and return contribution in our portfolio. Velocity is supported by high organic repeat rates.</p></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;"><div style="background:#111827;border:1px solid #1F2937;border-left:3px solid #C084FC;border-radius:8px;padding:12px 16px;font-size:12px;color:#94A3B8;"><strong style="color:#F8FAFC;">Lead Driver Focus:</strong> Double down on top 5 performing units to capture compounding scale.</div><div style="background:#111827;border:1px solid #1F2937;border-left:3px solid #FBBF24;border-radius:8px;padding:12px 16px;font-size:12px;color:#94A3B8;"><strong style="color:#F8FAFC;">Efficiency Expansion:</strong> Audit lower-velocity categories on the cost side to optimize margin.</div></div></div>''',
            "notes": speaker_notes.get("slide_4", f"On slide 4, {top_cat} is our clear anchor category. It produces the bulk of our gross margin. Our recommendation here is to double down on inventory depth for our top 5 SKUs while reviewing cost structures for trailing categories.")
        },
        {
            "num": "05",
            "name": "Action Plan",
            "icon": "📍",
            "tag": "STRATEGIC ROADMAP · SLIDE 05",
            "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:10px 0;"><div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-bottom:14px;">{meta.get("region_title", "Strategic Priorities & Next Steps")}</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;">{recs_grid_html}</div></div>''',
            "notes": speaker_notes.get("slide_5", f"Finally, slide 5 gives leadership four immediate action items: First, capture more market share in {top_region}; second, protect our {margin_str} margins; third, launch campaigns to lift {worst_month}; and fourth, test bundle add-ons to increase our {fmt(avg_order_val)} average order value.")
        },
    ]

    # Slide tab selectors
    tab_cols = st.columns(len(slides))
    for i, s in enumerate(slides):
        with tab_cols[i]:
            if st.button(f"{s['icon']} {s['num']} · {s['name']}", key=f"s_{i}", use_container_width=True,
                         type="primary" if i == st.session_state.slide_idx else "secondary"):
                st.session_state.slide_idx = i
                st.rerun()

    curr_s = slides[st.session_state.slide_idx]

    # 16:9 Slide Canvas Mockup
    st.markdown(f'''
    <div class="deck-viewport">
        <div class="deck-stage">
            <div class="slide-top-meta">
                <span class="slide-category-tag">{curr_s["tag"]}</span>
                <span class="slide-aspect-tag">16:9 Widescreen Presentation</span>
            </div>
            {curr_s["html"]}
            <div class="slide-footer-meta">
                <span>Analytics AutoPilot · Slide {curr_s["num"]} of 05</span>
                <span>{report_title} · Confidential</span>
            </div>
        </div>
        <div class="speaker-notes-box">
            <div style="font-size:11px;font-weight:700;color:#818CF8;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">
                🎤 Recommended Speaker Script (What to say during your meeting):
            </div>
            <div style="font-size:13px;color:#CBD5E1;line-height:1.6;font-style:italic;">
                "{curr_s["notes"]}"
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Slide Next/Prev controls
    c_prev, c_space, c_next = st.columns([1, 4, 1])
    with c_prev:
        if st.button("◀ Previous Slide", use_container_width=True, disabled=(st.session_state.slide_idx == 0)):
            st.session_state.slide_idx -= 1
            st.rerun()
    with c_next:
        if st.button("Next Slide ▶", use_container_width=True, disabled=(st.session_state.slide_idx == len(slides) - 1)):
            st.session_state.slide_idx += 1
            st.rerun()


    # ─────────────────────────────────────────────────────────────────────────────
    # POWERPOINT EXPORT PIPELINE (On-Demand & Cached for Instant Carousel Transitions)
    # ─────────────────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">One-Click Slide Deck Export</div>', unsafe_allow_html=True)

    if "pptx_cache" not in st.session_state:
        st.session_state.pptx_cache = {}

    active_trend  = st.session_state.get("ctrl_trend", trend_style)
    active_cat    = st.session_state.get("ctrl_cat", cat_style)
    active_region = st.session_state.get("ctrl_region", region_style)
    active_metric = st.session_state.get("ctrl_metric", top_metric)
    active_top_n  = st.session_state.get("ctrl_count", top_n)

    logo_name = logo_file.name if ('logo_file' in locals() and logo_file) else None
    bc_val = brand_color if 'brand_color' in locals() else None
    pptx_cache_key = (
        cache_key,
        active_trend,
        active_cat,
        active_region,
        active_metric,
        active_top_n,
        bc_val,
        logo_name,
        report_title,
        report_mode,
    )

    safe_title = report_title.replace(" ", "_")

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
        st.caption("✦ The slide preview above is generated instantly. Compile your 16:9 executive PowerPoint deck when you're ready to export.")
        if st.button("🚀  Generate Executive PowerPoint Deck (.pptx)", type="primary", use_container_width=True):
            with st.spinner("🎨 Rendering high-resolution chart PNGs and compiling PowerPoint deck..."):
                import tempfile
                from chart_engine   import generate_all_charts
                from slide_builder  import build_presentation

                # Synchronize ranking and aggregation dynamically with active metric and count
                clean_df = report_data.get("df", df)
                prod_col_name = "Product" if "Product" in clean_df.columns else ("Category" if "Category" in clean_df.columns else cat_col)
                agg_spec = {
                    "Revenue": ("Revenue", "sum"),
                    "Quantity": ("Quantity", "sum") if "Quantity" in clean_df.columns else ("Revenue", "count")
                }
                if has_profit and "Profit" in clean_df.columns:
                    agg_spec["Profit"] = ("Profit", "sum")
                else:
                    agg_spec["Profit"] = ("Revenue", lambda s: 0.0)

                sync_rank = clean_df.groupby(prod_col_name).agg(**agg_spec).reset_index().rename(columns={prod_col_name: "Product"})
                sync_rank = sync_rank.sort_values(active_metric, ascending=False).head(active_top_n)
                report_data["top_products"] = sync_rank

                chart_config = {
                    "trend_type":  active_trend,
                    "cat_type":    active_cat,
                    "region_type": active_region,
                    "top_metric":  active_metric,
                }

                # Isolated temporary directory ensures simultaneous users never overwrite each other's charts/decks
                with tempfile.TemporaryDirectory() as tmp_dir:
                    logo_path = None
                    if 'logo_file' in locals() and logo_file:
                        logo_ext = logo_file.name.split('.')[-1]
                        logo_path = os.path.join(tmp_dir, f"brand_logo.{logo_ext}")
                        with open(logo_path, "wb") as f:
                            f.write(logo_file.getbuffer())

                    chart_paths = generate_all_charts(report_data, config=chart_config, output_dir=tmp_dir)
                    pptx_path   = build_presentation(
                        report_data, chart_paths,
                        report_title=report_title,
                        narrative=narrative,
                        output_dir=tmp_dir,
                        brand_color=brand_color if 'brand_color' in locals() else None,
                        logo_path=logo_path
                    )
                    with open(pptx_path, "rb") as f:
                        pptx_bytes = f.read()

                st.session_state.pptx_cache[pptx_cache_key] = pptx_bytes
                st.rerun()

    st.caption("✦ Includes all generated charts, KPI summary cards, and speaker notes. Fully editable in PowerPoint & Google Slides.")

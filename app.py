"""
app.py  —  Analytics AutoPilot
3-Theme UI with live switcher: Linear Obsidian / Stripe Paper / Deck Studio
Run with:  python -m streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os, io

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Analytics AutoPilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# THEME DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────
THEMES = {
    "⚫  Linear Obsidian": "obsidian",
    "⚪  Stripe Paper":    "paper",
    "🖼️  Deck Studio":     "deck",
}

THEME_CSS = {

# ── 1. LINEAR OBSIDIAN ───────────────────────────────────────────────────────
"obsidian": """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #0A0D14 !important;
    font-family: 'Inter', sans-serif;
    color: #F1F5F9;
}
[data-testid="stSidebar"] { display: none; }
[data-testid="stHeader"]  { background: transparent !important; }

/* Top Nav */
.ap-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 18px 32px 14px;
    border-bottom: 1px solid #1E293B;
    margin-bottom: 32px;
}
.ap-logo { font-size: 17px; font-weight: 700; color: #6366F1; letter-spacing: -0.3px; }
.ap-logo span { color: #F1F5F9; }

/* Theme bar */
.theme-bar {
    background: #121826;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 14px 24px;
    margin: 0 32px 28px;
    display: flex; align-items: center; gap: 12px;
}
.theme-label { font-size: 11px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-right: 8px; }

/* Upload zone */
.upload-zone {
    border: 1.5px dashed #334155;
    border-radius: 16px;
    background: #0D1117;
    padding: 48px 32px;
    text-align: center;
    margin: 0 32px 28px;
    transition: border-color 0.2s;
}
.upload-zone:hover { border-color: #6366F1; }
.upload-title { font-size: 20px; font-weight: 600; color: #E2E8F0; margin-bottom: 8px; }
.upload-sub   { font-size: 13px; color: #64748B; }

/* KPI grid */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 0 32px 28px; }
.kpi {
    background: #121826;
    border: 1px solid #1E293B;
    border-radius: 14px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
}
.kpi::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #6366F1, #06B6D4);
}
.kpi-label { font-size: 11px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 10px; }
.kpi-value { font-size: 28px; font-weight: 700; color: #F1F5F9; letter-spacing: -0.5px; }
.kpi-pill  { display: inline-block; margin-top: 8px; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 20px; background: rgba(16,185,129,0.15); color: #10B981; }

/* Chart containers */
.chart-wrap { background: #121826; border: 1px solid #1E293B; border-radius: 14px; padding: 4px; margin-bottom: 20px; }

/* Insight cards */
.ins-card { background: #0F1724; border: 1px solid #1E293B; border-left: 3px solid #6366F1; border-radius: 10px; padding: 16px 18px; margin-bottom: 12px; }
.ins-title { font-size: 12px; font-weight: 700; color: #6366F1; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.06em; }
.ins-body  { font-size: 13px; color: #94A3B8; line-height: 1.6; }

/* Export button */
.section { margin: 0 32px; }
.section-head { font-size: 13px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid #1E293B; }

/* Streamlit widget overrides */
.stDownloadButton > button {
    background: linear-gradient(135deg, #6366F1, #4F46E5) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    padding: 14px !important; font-size: 14px !important;
}
.stDownloadButton > button:hover { opacity: 0.9 !important; }
div[data-testid="stFileUploader"] { margin: 0 32px; }
div[data-testid="stFileUploader"] > div {
    background: #0D1117 !important;
    border: 1.5px dashed #334155 !important;
    border-radius: 16px !important;
}
</style>
""",

# ── 2. STRIPE PAPER ──────────────────────────────────────────────────────────
"paper": """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #FAFAFA !important;
    font-family: 'Inter', sans-serif;
    color: #0F172A;
}
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stHeader"]  { background: transparent !important; }

.ap-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 20px 40px 18px;
    background: white;
    border-bottom: 1px solid #E5E7EB;
    margin-bottom: 0;
}
.ap-logo { font-family: 'Playfair Display', serif; font-size: 20px; color: #0F172A; }
.ap-logo span { color: #1D4ED8; }

/* Hero section */
.hero {
    background: white;
    border-bottom: 1px solid #E5E7EB;
    padding: 48px 40px 40px;
    margin-bottom: 32px;
}
.hero-eyebrow { font-size: 11px; font-weight: 600; color: #1D4ED8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 14px; }
.hero-title   { font-family: 'Playfair Display', serif; font-size: 36px; color: #0F172A; line-height: 1.2; margin-bottom: 12px; max-width: 560px; }
.hero-sub     { font-size: 15px; color: #64748B; max-width: 460px; line-height: 1.6; }

/* Theme bar */
.theme-bar {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 12px 20px;
    margin: 0 40px 28px;
    display: flex; align-items: center; gap: 10px;
}
.theme-label { font-size: 11px; font-weight: 600; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.07em; margin-right: 8px; }

/* Upload */
div[data-testid="stFileUploader"] { margin: 0 40px; }
div[data-testid="stFileUploader"] > div {
    background: white !important;
    border: 1.5px dashed #CBD5E1 !important;
    border-radius: 12px !important;
}

/* Executive summary callout */
.exec-summary {
    background: #EEF2FF;
    border-left: 4px solid #1D4ED8;
    border-radius: 10px;
    padding: 20px 24px;
    margin: 0 40px 28px;
}
.exec-summary-label { font-size: 11px; font-weight: 700; color: #1D4ED8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
.exec-summary-text  { font-size: 15px; color: #0F172A; line-height: 1.65; font-style: italic; }

/* KPI grid */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 0 40px 28px; }
.kpi {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 20px 22px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.04);
}
.kpi-label { font-size: 11px; font-weight: 600; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
.kpi-value { font-size: 26px; font-weight: 700; color: #0F172A; letter-spacing: -0.4px; }
.kpi-pill  { display: inline-block; margin-top: 7px; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 20px; background: #DCFCE7; color: #16A34A; }

/* Chart containers */
.chart-wrap { background: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 4px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }

/* Insight cards */
.ins-card { background: white; border: 1px solid #E5E7EB; border-radius: 10px; padding: 16px 20px; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
.ins-title { font-size: 12px; font-weight: 700; color: #1D4ED8; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.06em; }
.ins-body  { font-size: 13px; color: #374151; line-height: 1.6; }

.section { margin: 0 40px; }
.section-head { font-size: 13px; font-weight: 600; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #E5E7EB; }

.stDownloadButton > button {
    background: #1D4ED8 !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; padding: 14px !important; font-size: 14px !important;
}
.stDownloadButton > button:hover { background: #1E40AF !important; }
</style>
""",

# ── 3. DECK STUDIO ───────────────────────────────────────────────────────────
"deck": """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #0F172A !important;
    font-family: 'Inter', sans-serif;
    color: #E2E8F0;
}
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stHeader"]  { background: transparent !important; }

.ap-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 28px;
    background: #0F172A;
    border-bottom: 1px solid #1E293B;
    margin-bottom: 0;
}
.ap-logo { font-size: 15px; font-weight: 700; color: #E2E8F0; }
.ap-logo span { color: #38BDF8; }

/* Two-column layout */
.studio-wrap { display: flex; gap: 0; min-height: calc(100vh - 60px); }

/* Left tool rail */
.tool-rail {
    width: 240px; min-width: 240px;
    background: #0F172A;
    border-right: 1px solid #1E293B;
    padding: 24px 20px;
    flex-shrink: 0;
}
.rail-section { margin-bottom: 24px; }
.rail-label { font-size: 10px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px; }
.rail-item  { font-size: 13px; color: #CBD5E1; padding: 7px 10px; border-radius: 7px; cursor: pointer; margin-bottom: 2px; }
.rail-item:hover, .rail-item.active { background: #1E293B; color: #38BDF8; }

/* Canvas */
.slide-canvas {
    flex: 1;
    background: #E2E8F0;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 32px;
}
.slide-frame {
    width: 100%;
    max-width: 900px;
    aspect-ratio: 16/9;
    background: white;
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    overflow: hidden;
    position: relative;
}
.slide-nav {
    display: flex; align-items: center; gap: 16px;
    margin-top: 20px;
    color: #475569;
    font-size: 13px;
}
.slide-nav button {
    background: #0F172A; color: #E2E8F0;
    border: 1px solid #334155; border-radius: 7px;
    padding: 8px 16px; cursor: pointer; font-size: 13px;
    font-family: 'Inter', sans-serif;
}
.slide-nav button:hover { background: #1E293B; border-color: #38BDF8; color: #38BDF8; }

/* Theme bar */
.theme-bar {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 12px 20px;
    margin: 0 28px 24px;
    display: flex; align-items: center; gap: 10px;
}
.theme-label { font-size: 10px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.08em; margin-right: 8px; }

/* KPI strip */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 0 28px 24px; }
.kpi { background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 16px 18px; }
.kpi-label { font-size: 10px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 7px; }
.kpi-value { font-size: 22px; font-weight: 700; color: #E2E8F0; }
.kpi-pill  { display: inline-block; margin-top: 6px; font-size: 11px; font-weight: 600; padding: 2px 7px; border-radius: 20px; background: rgba(56,189,248,0.15); color: #38BDF8; }

.chart-wrap { background: #1E293B; border: 1px solid #334155; border-radius: 12px; padding: 4px; margin-bottom: 16px; }
.ins-card { background: #1E293B; border: 1px solid #334155; border-left: 3px solid #38BDF8; border-radius: 10px; padding: 14px 18px; margin-bottom: 10px; }
.ins-title { font-size: 11px; font-weight: 700; color: #38BDF8; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.06em; }
.ins-body  { font-size: 13px; color: #94A3B8; line-height: 1.6; }
.section { margin: 0 28px; }
.section-head { font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #1E293B; }

div[data-testid="stFileUploader"] { margin: 0 28px; }
div[data-testid="stFileUploader"] > div {
    background: #1E293B !important;
    border: 1.5px dashed #334155 !important;
    border-radius: 12px !important;
}
.stDownloadButton > button {
    background: #38BDF8 !important; color: #0F172A !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 700 !important; padding: 14px !important; font-size: 14px !important;
}
</style>
""",
}

# ─────────────────────────────────────────────────────────────────────────────
# CHART PALETTES PER THEME
# ─────────────────────────────────────────────────────────────────────────────
CHART_CFG = {
    "obsidian": dict(
        bg="#121826", paper="#121826", text="#94A3B8",
        grid="#1E293B", bar1="#6366F1", bar2="#10B981",
        palette=["#6366F1","#10B981","#06B6D4","#F59E0B","#EF4444"],
        line_bg="rgba(99,102,241,0.08)",
    ),
    "paper": dict(
        bg="#FFFFFF", paper="#FFFFFF", text="#374151",
        grid="#F3F4F6", bar1="#1D4ED8", bar2="#10B981",
        palette=["#1D4ED8","#10B981","#06B6D4","#F59E0B","#7C3AED"],
        line_bg="rgba(29,78,216,0.06)",
    ),
    "deck": dict(
        bg="#1E293B", paper="#1E293B", text="#94A3B8",
        grid="#334155", bar1="#38BDF8", bar2="#34D399",
        palette=["#38BDF8","#34D399","#A78BFA","#FBBF24","#F87171"],
        line_bg="rgba(56,189,248,0.08)",
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fmt(val):
    if   val >= 1_000_000: return f"${val/1_000_000:.2f}M"
    elif val >= 1_000:     return f"${val/1_000:.1f}K"
    return f"${val:,.0f}"

def kpi_block(label, value, pill=""):
    return f"""<div class="kpi">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {"<div class='kpi-pill'>"+pill+"</div>" if pill else ""}
    </div>"""

def insight(title, body):
    return f"""<div class="ins-card">
        <div class="ins-title">{title}</div>
        <div class="ins-body">{body}</div>
    </div>"""

def plotly_chart(fig, cc, title):
    fig.update_layout(
        paper_bgcolor=cc["paper"], plot_bgcolor=cc["bg"],
        font=dict(family="Inter, Arial", color=cc["text"]),
        title=dict(text=title, font=dict(size=14, color=cc["text"]), x=0.02),
        margin=dict(l=48, r=20, t=52, b=44),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=cc["text"])),
    )
    fig.update_xaxes(showgrid=False,  linecolor=cc["grid"], tickcolor=cc["grid"])
    fig.update_yaxes(showgrid=True,   gridcolor=cc["grid"], linecolor=cc["grid"])
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# RENDER: THEME PICKER + HEADER
# ─────────────────────────────────────────────────────────────────────────────
# Theme picker FIRST (before CSS injection so we know which CSS to load)
theme_choice = st.radio(
    "🎨 Theme",
    list(THEMES.keys()),
    horizontal=True,
    label_visibility="collapsed",
)
theme_key = THEMES[theme_choice]

# Inject CSS for chosen theme
st.markdown(THEME_CSS[theme_key], unsafe_allow_html=True)

# Nav bar
st.markdown(f"""
<div class="ap-nav">
    <div class="ap-logo">📊 Analytics <span>AutoPilot</span></div>
    <div style="font-size:12px;color:#64748B;">Raw data → Executive deck in seconds</div>
</div>""", unsafe_allow_html=True)

# Theme bar
theme_names = " &nbsp;|&nbsp; ".join(
    f"<b style='color:{"#6366F1" if theme_key=="obsidian" else "#1D4ED8" if theme_key=="paper" else "#38BDF8"}'>{k}</b>"
    if THEMES[k]==theme_key else f"<span style='color:#64748B'>{k}</span>"
    for k in THEMES
)
st.markdown(f"""
<div class="theme-bar">
    <span class="theme-label">Theme</span>
    {theme_names}
</div>""", unsafe_allow_html=True)

# Hero (Stripe Paper only)
if theme_key == "paper":
    st.markdown("""
    <div class="hero">
        <div class="hero-eyebrow">Analytics AutoPilot</div>
        <div class="hero-title">Your data, boardroom-ready.</div>
        <div class="hero-sub">Upload any spreadsheet and get a fully formatted executive presentation — KPIs, charts, talking points, and slides — in under 10 seconds.</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SETTINGS (inline, not sidebar)
# ─────────────────────────────────────────────────────────────────────────────
sc1, sc2, sc3 = st.columns([3, 2, 1])
with sc1:
    report_title = st.text_input("Report Title", value="2024 Sales Performance Report", label_visibility="collapsed")
with sc2:
    brand_color  = st.color_picker("Brand Color", "#6366F1" if theme_key == "obsidian" else "#1D4ED8" if theme_key == "paper" else "#38BDF8", label_visibility="collapsed")
with sc3:
    use_sample   = st.checkbox("Use sample data", value=False)

# ─────────────────────────────────────────────────────────────────────────────
# FILE UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Drop your CSV or Excel file here",
    type=["csv", "xlsx", "xls"],
    label_visibility="visible",
)

if not uploaded_file and not use_sample:
    cc = CHART_CFG[theme_key]
    color = "#6366F1" if theme_key == "obsidian" else "#1D4ED8" if theme_key == "paper" else "#38BDF8"
    st.markdown(f"""
    <div style="text-align:center;padding:48px 20px;color:{cc['text']};">
        <div style="font-size:40px;margin-bottom:16px;">📂</div>
        <div style="font-size:17px;font-weight:600;margin-bottom:8px;color:{color};">Drop a file or check "Use sample data" above</div>
        <div style="font-size:13px;opacity:0.6;">Supports CSV, Excel (.xlsx, .xls)</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("Loading data..."):
    if use_sample or uploaded_file is None:
        from generate_data import generate_sales_data
        df = generate_sales_data()
    else:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)

# ─────────────────────────────────────────────────────────────────────────────
# COLUMN MAPPING
# ─────────────────────────────────────────────────────────────────────────────
cols = df.columns.tolist()
def fcol(candidates):
    for c in candidates:
        for col in cols:
            if c.lower() in col.lower(): return col
    return cols[0]

date_col    = fcol(["date","time","day","month"])
revenue_col = fcol(["revenue","sales","amount","income","total"])
profit_col  = fcol(["profit","margin","net"])
cost_col    = fcol(["cost","expense","cogs"])
cat_col     = fcol(["category","type","segment"])
region_col  = fcol(["region","area","zone","location"])

with st.expander("⚙️ Column Mapping (auto-detected — click to adjust)", expanded=False):
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        date_col    = st.selectbox("Date",     cols, index=cols.index(date_col))
        revenue_col = st.selectbox("Revenue",  cols, index=cols.index(revenue_col))
    with mc2:
        profit_col  = st.selectbox("Profit",   cols, index=cols.index(profit_col))
        cost_col    = st.selectbox("Cost",      cols, index=cols.index(cost_col))
    with mc3:
        cat_col     = st.selectbox("Category", cols, index=cols.index(cat_col))
        region_col  = st.selectbox("Region",   cols, index=cols.index(region_col))

generate = st.button("⚡  Generate Report", type="primary", use_container_width=True)
if not generate:
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("Analysing..."):
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["_month"] = df[date_col].dt.to_period("M")

    total_revenue  = df[revenue_col].sum()
    total_profit   = df[profit_col].sum()
    total_cost     = df[cost_col].sum()
    total_orders   = len(df)
    profit_margin  = total_profit / total_revenue * 100 if total_revenue else 0
    avg_order_val  = df[revenue_col].mean()

    monthly = (df.groupby("_month")
                 .agg(Revenue=(revenue_col,"sum"), Profit=(profit_col,"sum"))
                 .reset_index())
    monthly["Month_Label"] = monthly["_month"].dt.strftime("%b %Y")
    monthly["MoM_Growth"]  = monthly["Revenue"].pct_change() * 100

    category = (df.groupby(cat_col)
                  .agg(Revenue=(revenue_col,"sum"), Profit=(profit_col,"sum"))
                  .reset_index().sort_values("Revenue", ascending=False))
    category["Margin_%"] = (category["Profit"] / category["Revenue"] * 100).round(1)

    region_df = (df.groupby(region_col)
                   .agg(Revenue=(revenue_col,"sum"))
                   .reset_index().sort_values("Revenue", ascending=False))

    best_month  = monthly.loc[monthly["Revenue"].idxmax(), "Month_Label"]
    worst_month = monthly.loc[monthly["Revenue"].idxmin(), "Month_Label"]
    top_cat     = category.iloc[0][cat_col]
    top_region  = region_df.iloc[0][region_col]
    mom_avg     = monthly["MoM_Growth"].mean()

cc = CHART_CFG[theme_key]

# ─────────────────────────────────────────────────────────────────────────────
# PAPER THEME: Executive Summary Callout
# ─────────────────────────────────────────────────────────────────────────────
if theme_key == "paper":
    st.markdown(f"""
    <div class="exec-summary">
        <div class="exec-summary-label">Executive Summary</div>
        <div class="exec-summary-text">
            {best_month} delivered peak performance, with <strong>{top_cat}</strong>
            as the standout category. Profit margins held at a healthy
            <strong>{profit_margin:.1f}%</strong> across {total_orders:,} transactions.
            {top_region} leads all regions. Weakest period: {worst_month} — a targeted
            promotional window for next year.
        </div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section"><div class="section-head">Key Performance Indicators</div></div>', unsafe_allow_html=True)

kpis_html = "".join([
    kpi_block("Total Revenue",   fmt(total_revenue),  f"↑ {mom_avg:.1f}% avg MoM"),
    kpi_block("Total Profit",    fmt(total_profit),   "After all costs"),
    kpi_block("Profit Margin",   f"{profit_margin:.1f}%", "✓ Above 35% target"),
    kpi_block("Total Orders",    f"{total_orders:,}",  f"Avg {fmt(avg_order_val)}"),
])
st.markdown(f'<div class="kpi-grid">{kpis_html}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────────────────────
import plotly.graph_objects as go

st.markdown('<div class="section"><div class="section-head">Charts & Trends</div></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=monthly["Month_Label"], y=monthly["Revenue"],
                          name="Revenue", marker_color=cc["bar1"], opacity=0.9))
    fig1.add_trace(go.Bar(x=monthly["Month_Label"], y=monthly["Profit"],
                          name="Profit",  marker_color=cc["bar2"], opacity=0.9))
    fig1.update_layout(barmode="group")
    fig1.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(plotly_chart(fig1, cc, "Monthly Revenue & Profit"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    fig2 = go.Figure(go.Bar(
        x=category["Revenue"], y=category[cat_col], orientation="h",
        marker_color=cc["palette"][:len(category)],
        text=[f"${v:,.0f}  ({m:.1f}%)" for v, m in zip(category["Revenue"], category["Margin_%"])],
        textposition="outside", textfont=dict(color=cc["text"]),
    ))
    fig2.update_xaxes(tickprefix="$", tickformat=",.0f")
    fig2.update_yaxes(autorange="reversed")
    st.plotly_chart(plotly_chart(fig2, cc, f"Revenue by {cat_col}"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

col3, col4 = st.columns(2)
with col3:
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    fig3 = go.Figure(go.Pie(
        labels=region_df[region_col], values=region_df["Revenue"],
        hole=0.45,
        marker=dict(colors=cc["palette"][:len(region_df)], line=dict(color=cc["bg"], width=2)),
        textinfo="label+percent", textfont=dict(color=cc["text"]),
    ))
    fig3.update_layout(paper_bgcolor=cc["paper"], font=dict(color=cc["text"]),
                       title=dict(text=f"Revenue by {region_col}", font=dict(size=14, color=cc["text"]), x=0.02),
                       margin=dict(l=20,r=20,t=52,b=20),
                       legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=cc["text"])))
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=monthly["Month_Label"], y=monthly["Revenue"],
        mode="lines+markers", name="Revenue",
        line=dict(color=cc["bar1"], width=2.5),
        marker=dict(size=7, color=cc["bar1"]),
        fill="tozeroy", fillcolor=cc["line_bg"],
    ))
    fig4.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(plotly_chart(fig4, cc, "Revenue Trend"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DECK STUDIO: Slide Carousel Preview
# ─────────────────────────────────────────────────────────────────────────────
if theme_key == "deck":
    st.markdown('<div class="section"><div class="section-head">Slide Preview</div></div>', unsafe_allow_html=True)

    if "slide_idx" not in st.session_state:
        st.session_state.slide_idx = 0

    slides = [
        {"title": "Title Slide",        "icon": "🏷️",  "preview": f"<h2 style='margin:0;font-size:28px;font-weight:700;color:#0F172A;'>2024 Sales Performance Report</h2><p style='color:#64748B;margin-top:12px;font-size:14px;'>Analytics AutoPilot · November 2026</p>"},
        {"title": "KPI Overview",       "icon": "📌", "preview": f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;'><div style='background:#EEF2FF;border-radius:8px;padding:14px;'><div style='font-size:11px;color:#1D4ED8;font-weight:700;'>TOTAL REVENUE</div><div style='font-size:24px;font-weight:700;color:#0F172A;'>{fmt(total_revenue)}</div></div><div style='background:#F0FDF4;border-radius:8px;padding:14px;'><div style='font-size:11px;color:#16A34A;font-weight:700;'>TOTAL PROFIT</div><div style='font-size:24px;font-weight:700;color:#0F172A;'>{fmt(total_profit)}</div></div><div style='background:#FEF3C7;border-radius:8px;padding:14px;'><div style='font-size:11px;color:#D97706;font-weight:700;'>PROFIT MARGIN</div><div style='font-size:24px;font-weight:700;color:#0F172A;'>{profit_margin:.1f}%</div></div><div style='background:#F5F3FF;border-radius:8px;padding:14px;'><div style='font-size:11px;color:#7C3AED;font-weight:700;'>TOTAL ORDERS</div><div style='font-size:24px;font-weight:700;color:#0F172A;'>{total_orders:,}</div></div></div>"},
        {"title": "Monthly Trend",      "icon": "📈", "preview": "<div style='text-align:center;padding:20px;color:#64748B;font-size:14px;'>📊 Monthly Revenue & Profit bar chart<br><br>Peak: <strong style='color:#0F172A;'>"+best_month+"</strong> · Lowest: <strong style='color:#0F172A;'>"+worst_month+"</strong></div>"},
        {"title": "Category & Products","icon": "🏆", "preview": f"<div style='text-align:center;padding:20px;color:#64748B;font-size:14px;'>🏷️ Revenue by category breakdown<br><br>Top category: <strong style='color:#0F172A;'>{top_cat}</strong><br>Avg margin: <strong style='color:#0F172A;'>{profit_margin:.1f}%</strong></div>"},
        {"title": "Regional & Actions", "icon": "📍", "preview": f"<div style='text-align:center;padding:20px;color:#64748B;font-size:14px;'>📍 Regional revenue donut + action cards<br><br>Leading region: <strong style='color:#0F172A;'>{top_region}</strong><br>Key action: Focus Q1 budget here</div>"},
    ]

    idx = st.session_state.slide_idx
    slide = slides[idx]

    # Slide tabs
    tab_cols = st.columns(5)
    for i, s in enumerate(slides):
        with tab_cols[i]:
            if st.button(f"{s['icon']} {s['title']}", key=f"slide_tab_{i}",
                         use_container_width=True,
                         type="primary" if i == idx else "secondary"):
                st.session_state.slide_idx = i
                st.rerun()

    # Slide frame
    st.markdown(f"""
    <div style="background:#E2E8F0;border-radius:12px;padding:24px;margin-top:12px;">
        <div style="background:white;border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,0.15);
                    padding:40px;min-height:260px;display:flex;flex-direction:column;justify-content:center;">
            <div style="font-size:11px;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:16px;">
                Slide {idx+1} of {len(slides)}  ·  {slide['title']}
            </div>
            {slide['preview']}
        </div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INSIGHTS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section"><div class="section-head">Executive Insights</div></div>', unsafe_allow_html=True)

ins1, ins2 = st.columns(2)
with ins1:
    st.markdown(insight("📈 Peak Month",    f"<strong>{best_month}</strong> was your strongest month. Align inventory and campaigns to this window next year."), unsafe_allow_html=True)
    st.markdown(insight("🏆 Top Category",  f"<strong>{top_cat}</strong> leads by revenue. Expand the product range here to capture more margin."), unsafe_allow_html=True)
    st.markdown(insight("📍 Top Region",    f"<strong>{top_region}</strong> is your highest-revenue market. Use it as the launchpad for new SKUs."), unsafe_allow_html=True)
with ins2:
    st.markdown(insight("⚠️ Weak Period",   f"<strong>{worst_month}</strong> was your softest month. Plan promotions or bundle deals early for this window."), unsafe_allow_html=True)
    st.markdown(insight("💰 Margin Health", f"Margin at <strong>{profit_margin:.1f}%</strong>. {'Healthy — well above 35% threshold ✅' if profit_margin > 35 else 'Below target — review cost structure ⚠️'}."), unsafe_allow_html=True)
    st.markdown(insight("🛒 Order Value",   f"Avg order is <strong>{fmt(avg_order_val)}</strong>. Upsell bundles or add-ons could move this 10–15% higher."), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section"><div class="section-head">Export</div></div>', unsafe_allow_html=True)

with st.spinner("Building PowerPoint deck..."):
    monthly_export = monthly.copy()
    if "Product" in df.columns and "Quantity" in df.columns:
        top_products = (df.groupby("Product")
                          .agg(Revenue=(revenue_col,"sum"), Quantity=("Quantity","sum"))
                          .reset_index().sort_values("Revenue", ascending=False).head(5))
    else:
        top_products = category.rename(columns={cat_col:"Product"}).head(5)
        top_products["Quantity"] = 0

    report_data = {
        "kpis": {
            "total_revenue":   round(total_revenue,2),
            "total_profit":    round(total_profit,2),
            "total_cost":      round(total_cost,2),
            "total_orders":    total_orders,
            "total_units":     int(df["Quantity"].sum()) if "Quantity" in df.columns else 0,
            "avg_order_value": round(avg_order_val,2),
            "profit_margin":   round(profit_margin,2),
            "return_rate":     round((df["Returned"].sum()/total_orders*100),2) if "Returned" in df.columns else 0,
        },
        "monthly":      monthly_export,
        "category":     category,
        "region":       region_df.rename(columns={region_col:"Region"}),
        "top_products": top_products,
        "channels":     pd.DataFrame({"Channel":["N/A"],"Revenue":[0],"Orders":[0],"Revenue_%":[100]}),
        "insights": {
            "best_month": best_month, "worst_month": worst_month,
            "avg_mom_growth": round(mom_avg,2) if not pd.isna(mom_avg) else 0,
            "top_category": top_cat, "top_region": top_region, "top_channel": "N/A",
        }
    }

    os.makedirs(os.path.join(os.path.dirname(__file__), "output"), exist_ok=True)
    from chart_engine   import generate_all_charts
    from slide_builder  import build_presentation
    chart_paths = generate_all_charts(report_data)
    pptx_path   = build_presentation(report_data, chart_paths)

    with open(pptx_path, "rb") as f:
        pptx_bytes = f.read()

safe_title = report_title.replace(" ", "_")
st.download_button(
    label="📥  Download PowerPoint Presentation (.pptx)",
    data=pptx_bytes,
    file_name=f"{safe_title}.pptx",
    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    use_container_width=True,
    type="primary",
)
st.markdown("""<p style="text-align:center;font-size:12px;opacity:0.5;margin-top:8px;">
    Fully editable in Microsoft PowerPoint or Google Slides</p>""", unsafe_allow_html=True)

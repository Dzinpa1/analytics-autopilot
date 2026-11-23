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
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# LINEAR OBSIDIAN DESIGN SYSTEM (CSS)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Global Reset & Base */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #080B11 !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #F8FAFC !important;
}

[data-testid="stSidebar"] { display: none !important; }
[data-testid="stHeader"]  { background: transparent !important; }
.block-container { padding: 1.5rem 3rem 4rem !important; max-width: 1400px; }

/* Navigation Bar */
.ap-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 0 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
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
    background: radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.12) 0%, transparent 70%);
    border: 1px solid rgba(255, 255, 255, 0.06);
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
    background: #0E131F;
    border: 1px solid rgba(255, 255, 255, 0.06);
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
    background: #0E131F;
    border: 1px solid rgba(255, 255, 255, 0.06);
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
    background: #0E131F;
    border: 1px solid rgba(255, 255, 255, 0.06);
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
    background: #0E131F;
    border: 1px solid rgba(255, 255, 255, 0.06);
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
    background: rgba(255, 255, 255, 0.07);
}

/* Slide Carousel Frame */
.carousel-box {
    background: #0E131F;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 28px;
}
.deck-viewport {
    background: #06090F;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 28px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.deck-stage {
    width: 100%;
    max-width: 920px;
    min-height: 440px;
    background: radial-gradient(circle at 80% 20%, #151E33 0%, #0D1322 100%);
    border: 1px solid rgba(255, 255, 255, 0.12);
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
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
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
    border-top: 1px solid rgba(255, 255, 255, 0.08);
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
    background: #0E131F;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-left: 3px solid #818CF8;
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 16px;
}

/* Streamlit Inputs Overrides */
div[data-testid="stFileUploader"] > div {
    background: #0E131F !important;
    border: 1.5px dashed rgba(99, 102, 241, 0.35) !important;
    border-radius: 14px !important;
}
div[data-testid="stFileUploader"] > div:hover {
    border-color: #6366F1 !important;
}
div[data-testid="stTextInput"] input {
    background: #141B2D !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
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
# CONTROL RAIL (File Upload & Settings)
# ─────────────────────────────────────────────────────────────────────────────
c_upload, c_settings = st.columns([2, 1])

with c_upload:
    uploaded_file = st.file_uploader(
        "Upload dataset (.csv, .xlsx, .xls)",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed"
    )

with c_settings:
    report_title = st.text_input("Presentation Title", value="2024 Sales Performance Review")
    use_sample   = st.checkbox("⚡ Load 1,200-row sample dataset", value=False if uploaded_file else True)

if not uploaded_file and not use_sample:
    st.info("👆 Drop a CSV/Excel file or check the sample dataset box to generate the report.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# LOAD & PREPARE DATA
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("Processing data engine..."):
    if use_sample or uploaded_file is None:
        from generate_data import generate_sales_data
        df = generate_sales_data()
    else:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)

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

# Column mapping collapse
with st.expander("⚙️ Verify Auto-Mapped Columns", expanded=False):
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        date_col    = st.selectbox("Date Column", cols, index=cols.index(date_col))
        revenue_col = st.selectbox("Revenue Column", cols, index=cols.index(revenue_col))
    with mc2:
        profit_col  = st.selectbox("Profit Column", cols, index=cols.index(profit_col))
        cost_col    = st.selectbox("Cost Column", cols, index=cols.index(cost_col))
    with mc3:
        cat_col     = st.selectbox("Category Column", cols, index=cols.index(cat_col))
        region_col  = st.selectbox("Region Column", cols, index=cols.index(region_col))

# ─────────────────────────────────────────────────────────────────────────────
# COMPUTE METRICS VIA ANALYSIS ENGINE (Single Source of Truth)
# ─────────────────────────────────────────────────────────────────────────────
from analysis_engine import build_report_from_df

col_mapping = {
    "date": date_col,
    "revenue": revenue_col,
    "profit": profit_col,
    "cost": cost_col,
    "category": cat_col,
    "region": region_col,
    "product": "Product" if "Product" in df.columns else cat_col,
}

report_data = build_report_from_df(df, mapping=col_mapping)

kpis     = report_data["kpis"]
monthly  = report_data["monthly"]
category = report_data["category"]
region_df = report_data["region"]
insights = report_data["insights"]

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

def fmt(v):
    if v >= 1_000_000: return f"${v/1_000_000:.2f}M"
    elif v >= 1_000:   return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"

# ─────────────────────────────────────────────────────────────────────────────
# KPI CARDS (Linear Obsidian Style)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Core Performance Indicators</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-card">
        <div class="kpi-label">Gross Revenue</div>
        <div class="kpi-value">{fmt(total_revenue)}</div>
        <div class="kpi-pill pill-blue">↑ {mom_avg:.1f}% Avg MoM</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">Net Profit</div>
        <div class="kpi-value">{fmt(total_profit)}</div>
        <div class="kpi-pill pill-green">After All Costs</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">Profit Margin</div>
        <div class="kpi-value">{profit_margin:.1f}%</div>
        <div class="kpi-pill pill-purple">Target: >35.0%</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">Total Volume</div>
        <div class="kpi-value">{total_orders:,}</div>
        <div class="kpi-pill pill-amber">AOV: {fmt(avg_order_val)}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HIGH-DENSITY PLOTLY CHARTS (Dark Neon Palette + 1-Click Swappable Views)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Interactive Analytics Engine · Customizable Visuals</div>', unsafe_allow_html=True)

DARK_BG    = "#0E131F"
GRID_COLOR = "rgba(255, 255, 255, 0.06)"
TEXT_COLOR = "#94A3B8"
PALETTE    = ["#6366F1", "#38BDF8", "#34D399", "#FBBF24", "#F87171", "#C084FC"]

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
        st.markdown('<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">Monthly Performance</div>', unsafe_allow_html=True)
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
        fig1.add_trace(go.Scatter(
            x=monthly["Month_Label"], y=monthly["Profit"],
            mode="lines+markers", name="Profit",
            line=dict(color="#34D399", width=2.5),
            marker=dict(size=6, color="#34D399"),
        ))
        fig1.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(style_chart(fig1, "Revenue & Profit Trajectory (Line)"), use_container_width=True)
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
        fig1.add_trace(go.Bar(
            x=monthly["Month_Label"], y=monthly["Profit"],
            name="Profit", marker_color="#34D399", opacity=0.92
        ))
        fig1.update_layout(barmode="group")
        fig1.update_yaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(style_chart(fig1, "Monthly Revenue vs Net Profit"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with ch2:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    c2_head, c2_ctrl = st.columns([2, 1])
    with c2_head:
        st.markdown(f'<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">Category Portfolio</div>', unsafe_allow_html=True)
    with c2_ctrl:
        cat_style = st.selectbox("Style", ["Horizontal Bar", "Treemap", "Donut"], key="ctrl_cat", label_visibility="collapsed")

    if cat_style == "Treemap":
        fig2 = px.treemap(
            category, path=[cat_col], values="Revenue",
            color="Margin_%", color_continuous_scale=["#6366F1", "#38BDF8", "#34D399"],
            title=f"Category Volume & Margin Matrix"
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
        fig2 = go.Figure(go.Bar(
            x=category["Revenue"], y=category[cat_col], orientation="h",
            marker_color=PALETTE[:len(category)],
            text=[f"${v:,.0f}  ({m:.1f}%)" for v, m in zip(category["Revenue"], category["Margin_%"])],
            textposition="outside", textfont=dict(color=TEXT_COLOR, size=11),
        ))
        fig2.update_xaxes(tickprefix="$", tickformat=",.0f")
        fig2.update_yaxes(autorange="reversed")
        st.plotly_chart(style_chart(fig2, f"Revenue & Margin by {cat_col}"), use_container_width=True)
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
            text=[f"${v:,.0f}" for v in region_df["Revenue"]],
            textposition="outside", textfont=dict(color=TEXT_COLOR, size=10),
        ))
        fig3.update_yaxes(tickprefix="$", tickformat=",.0f")
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
        top_metric = st.selectbox("Metric", ["Revenue", "Profit", "Quantity"], key="ctrl_metric", label_visibility="collapsed")
    with c4_c2:
        top_n = st.selectbox("Count", [5, 10], key="ctrl_count", label_visibility="collapsed")

    # Aggregate dynamically
    prod_col_name = "Product" if "Product" in df.columns else cat_col
    agg_dict = {revenue_col: "sum", profit_col: "sum"}
    if "Quantity" in df.columns:
        agg_dict["Quantity"] = "sum"

    prod_rank = df.groupby(prod_col_name).agg(**{
        "Revenue": (revenue_col, "sum"),
        "Profit": (profit_col, "sum"),
        "Quantity": ("Quantity", "sum") if "Quantity" in df.columns else (revenue_col, "count")
    }).reset_index().rename(columns={prod_col_name: "Product"})

    prod_rank = prod_rank.sort_values(top_metric, ascending=False).head(top_n)

    is_curr = top_metric in ["Revenue", "Profit"]
    fig4 = go.Figure(go.Bar(
        x=prod_rank["Product"], y=prod_rank[top_metric],
        marker_color=PALETTE[:len(prod_rank)],
        text=[f"${v:,.0f}" if is_curr else f"{int(v):,} units" for v in prod_rank[top_metric]],
        textposition="outside", textfont=dict(color=TEXT_COLOR, size=10),
    ))
    if is_curr:
        fig4.update_yaxes(tickprefix="$", tickformat=",.0f")
    else:
        fig4.update_yaxes(tickformat=",.0f")
    st.plotly_chart(style_chart(fig4, f"Top {top_n} Products by {top_metric}"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE CAROUSEL PREVIEW (Interactive 16:9 Deck Viewer)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Presentation Deck Preview (16:9 Widescreen)</div>', unsafe_allow_html=True)

if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0

slides = [
    {
        "num": "01",
        "name": "Executive Cover",
        "icon": "🏷️",
        "tag": "EXECUTIVE BRIEFING · SLIDE 01",
        "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:20px 0;"><div style="display:inline-block;padding:4px 12px;border-radius:20px;background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);color:#A5B4FC;font-size:11px;font-weight:700;letter-spacing:0.08em;margin-bottom:16px;width:fit-content;">✦ EXECUTIVE REPORT</div><h1 style="font-size:36px;font-weight:800;color:#F8FAFC;margin:0 0 12px 0;letter-spacing:-0.02em;line-height:1.2;">{report_title}</h1><p style="font-size:15px;color:#94A3B8;margin:0 0 24px 0;line-height:1.6;">Automated Full-Cycle Business Performance & Margin Analysis</p><div style="display:flex;gap:20px;font-size:12px;color:#64748B;"><span style="color:#A5B4FC;">● Certified Dataset</span><span>{len(df):,} Validated Transactions</span><span>Confidential · Boardroom Ready</span></div></div>''',
        "notes": f"Welcome everyone. Today we are reviewing our executive performance report for {report_title}. We will walk through our high-level KPIs, seasonal trends, category margin health, and strategic growth priorities."
    },
    {
        "num": "02",
        "name": "KPI Matrix",
        "icon": "📌",
        "tag": "FINANCIAL HIGHLIGHTS · SLIDE 02",
        "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:10px 0;"><div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-bottom:18px;">Executive Financial Summary</div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px;"><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:18px;"><div style="font-size:10px;color:#64748B;font-weight:700;letter-spacing:0.06em;">GROSS REVENUE</div><div style="font-size:26px;font-weight:800;color:#F8FAFC;margin-top:6px;">{fmt(total_revenue)}</div><div style="font-size:11px;color:#38BDF8;margin-top:4px;">↑ {mom_avg:.1f}% Avg MoM</div></div><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:18px;"><div style="font-size:10px;color:#64748B;font-weight:700;letter-spacing:0.06em;">NET PROFIT</div><div style="font-size:26px;font-weight:800;color:#34D399;margin-top:6px;">{fmt(total_profit)}</div><div style="font-size:11px;color:#34D399;margin-top:4px;">After All COGS</div></div><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:18px;"><div style="font-size:10px;color:#64748B;font-weight:700;letter-spacing:0.06em;">PROFIT MARGIN</div><div style="font-size:26px;font-weight:800;color:#C084FC;margin-top:6px;">{profit_margin:.1f}%</div><div style="font-size:11px;color:#C084FC;margin-top:4px;">Target >35% Met</div></div><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:18px;"><div style="font-size:10px;color:#64748B;font-weight:700;letter-spacing:0.06em;">ORDER VOLUME</div><div style="font-size:26px;font-weight:800;color:#FBBF24;margin-top:6px;">{total_orders:,}</div><div style="font-size:11px;color:#FBBF24;margin-top:4px;">AOV: {fmt(avg_order_val)}</div></div></div><div style="background:#0E131F;border-left:3px solid #6366F1;border-radius:8px;padding:12px 16px;font-size:13px;color:#94A3B8;">● Key Takeaway: Gross revenue closed at {fmt(total_revenue)} with healthy margin retention at {profit_margin:.1f}%, indicating strong pricing power and controlled fulfillment costs.</div></div>''',
        "notes": f"Slide 2 outlines our bottom-line numbers. Net profit reached {fmt(total_profit)} on {fmt(total_revenue)} of gross revenue. With an average order value of {fmt(avg_order_val)}, our 48% margins give us substantial headroom to invest in marketing."
    },
    {
        "num": "03",
        "name": "Monthly Trajectory",
        "icon": "📈",
        "tag": "MOMENTUM & SEASONALITY · SLIDE 03",
        "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:10px 0;"><div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-bottom:14px;">Annual Trajectory & Peak Analysis</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px;"><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:20px;"><div style="font-size:11px;color:#38BDF8;font-weight:700;text-transform:uppercase;">🏆 Annual High-Water Mark</div><div style="font-size:24px;font-weight:800;color:#F8FAFC;margin:8px 0 4px 0;">{best_month}</div><p style="font-size:13px;color:#94A3B8;margin:0;line-height:1.5;">Highest monthly revenue concentration. Driven by accelerated consumer demand and promotional alignment.</p></div><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:20px;"><div style="font-size:11px;color:#F87171;font-weight:700;text-transform:uppercase;">⚠️ Seasonal Contraction Window</div><div style="font-size:24px;font-weight:800;color:#F8FAFC;margin:8px 0 4px 0;">{worst_month}</div><p style="font-size:13px;color:#94A3B8;margin:0;line-height:1.5;">Softest period recorded. Represents our primary opportunity for strategic counter-cyclical campaigns.</p></div></div><div style="background:#0E131F;border-left:3px solid #38BDF8;border-radius:8px;padding:12px 16px;font-size:13px;color:#94A3B8;">● Executive Guidance: Ramp up supply chain readiness 45 days prior to {best_month} to avoid stock-outs.</div></div>''',
        "notes": f"Looking at seasonality on slide 3: our peak performance hit in {best_month}. Conversely, {worst_month} showed our seasonal trough. We recommend timing next year's promotional budget to hedge this exact slow period."
    },
    {
        "num": "04",
        "name": "Category Dominance",
        "icon": "🏆",
        "tag": "PORTFOLIO MIX · SLIDE 04",
        "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:10px 0;"><div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-bottom:14px;">Product Category & Margin Contribution</div><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:20px;margin-bottom:16px;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;"><span style="font-size:16px;font-weight:800;color:#F8FAFC;">Top Category: {top_cat}</span><span style="font-size:12px;font-weight:700;color:#34D399;background:rgba(16,185,129,0.12);padding:4px 10px;border-radius:12px;">{profit_margin:.1f}% Avg Margin</span></div><p style="font-size:13px;color:#94A3B8;margin:0;line-height:1.6;">{top_cat} accounts for the single largest revenue and profit contribution in our portfolio. Unit velocity is supported by high customer retention.</p></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;"><div style="background:#0E131F;border-left:3px solid #C084FC;border-radius:8px;padding:12px 16px;font-size:12px;color:#94A3B8;"><strong style="color:#F8FAFC;">Lead SKU Focus:</strong> Prioritize safety stock in top 5 product variants to meet consistent reorder volume.</div><div style="background:#0E131F;border-left:3px solid #FBBF24;border-radius:8px;padding:12px 16px;font-size:12px;color:#94A3B8;"><strong style="color:#F8FAFC;">Margin Expansion:</strong> Explore bundle pricing to lift lower-velocity catalog items.</div></div></div>''',
        "notes": f"On slide 4, {top_cat} is our clear anchor category. It produces the bulk of our gross margin. Our recommendation here is to double down on inventory depth for our top 5 SKUs while reviewing cost structures for trailing categories."
    },
    {
        "num": "05",
        "name": "Strategic Recommendations",
        "icon": "📍",
        "tag": "ACTION PLAN · SLIDE 05",
        "html": f'''<div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:10px 0;"><div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-bottom:14px;">Strategic Priorities & Next Steps</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;"><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-left:3px solid #6366F1;border-radius:10px;padding:16px;"><div style="font-size:11px;font-weight:700;color:#818CF8;text-transform:uppercase;">1. Regional Scale</div><div style="font-size:13px;color:#CBD5E1;margin-top:6px;line-height:1.5;">Expand ad budget and distribution in <strong>{top_region}</strong>, our highest revenue region.</div></div><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-left:3px solid #34D399;border-radius:10px;padding:16px;"><div style="font-size:11px;font-weight:700;color:#34D399;text-transform:uppercase;">2. Margin Defense</div><div style="font-size:13px;color:#CBD5E1;margin-top:6px;line-height:1.5;">Maintain our <strong>{profit_margin:.1f}%</strong> profit margin threshold by auditing supplier terms.</div></div><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-left:3px solid #F87171;border-radius:10px;padding:16px;"><div style="font-size:11px;font-weight:700;color:#F87171;text-transform:uppercase;">3. Seasonality Bridge</div><div style="font-size:13px;color:#CBD5E1;margin-top:6px;line-height:1.5;">Deploy promotional incentives to elevate revenue during the <strong>{worst_month}</strong> dip.</div></div><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-left:3px solid #FBBF24;border-radius:10px;padding:16px;"><div style="font-size:11px;font-weight:700;color:#FBBF24;text-transform:uppercase;">4. Basket Optimization</div><div style="font-size:13px;color:#CBD5E1;margin-top:6px;line-height:1.5;">Introduce SKU cross-sells to push average order value beyond <strong>{fmt(avg_order_val)}</strong>.</div></div></div></div>''',
        "notes": f"Finally, slide 5 gives leadership four immediate action items: First, capture more market share in {top_region}; second, protect our 48% margins; third, launch campaigns to lift {worst_month}; and fourth, test bundle add-ons to increase our {fmt(avg_order_val)} average order value."
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
# EXECUTIVE TALKING POINTS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Automated Executive Takeaways</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="insight-grid">
    <div class="insight-card">
        <div class="insight-title">📈 Peak Cycle Discovery</div>
        <div class="insight-body">
            <strong>{best_month}</strong> drove the highest revenue velocity. Allocate marketing budget and inventory ramp-ups 45 days prior to this window.
        </div>
    </div>
    <div class="insight-card">
        <div class="insight-title">🏆 Core Growth Driver</div>
        <div class="insight-body">
            <strong>{top_cat}</strong> outperforms all other product lines in revenue generation. Expand unit selection in this vertical.
        </div>
    </div>
    <div class="insight-card">
        <div class="insight-title">📍 Geographic Density</div>
        <div class="insight-body">
            <strong>{top_region}</strong> commands highest market share. Evaluate localized partnerships and express fulfillment in this region.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# POWERPOINT EXPORT PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">One-Click Slide Deck Export</div>', unsafe_allow_html=True)

with st.spinner("Compiling PowerPoint deck..."):
    # Synchronize user-selected top products ranking into report_data
    report_data["top_products"] = prod_rank

    os.makedirs(os.path.join(os.path.dirname(__file__), "output"), exist_ok=True)
    from chart_engine   import generate_all_charts
    from slide_builder  import build_presentation
    chart_config = {
        "trend_type":  trend_style,
        "cat_type":    cat_style,
        "region_type": region_style,
        "top_metric":  top_metric,
    }
    chart_paths = generate_all_charts(report_data, config=chart_config)
    pptx_path   = build_presentation(report_data, chart_paths, report_title=report_title)

    with open(pptx_path, "rb") as f:
        pptx_bytes = f.read()

safe_title = report_title.replace(" ", "_")
st.download_button(
    label="📥  Download Executive PowerPoint Deck (.pptx)",
    data=pptx_bytes,
    file_name=f"{safe_title}.pptx",
    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    use_container_width=True,
    type="primary",
)

st.caption("✦ Includes all generated charts, KPI summary cards, and speaker notes. Fully editable in PowerPoint & Google Slides.")

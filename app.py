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
.slide-mockup {
    background: #141B2D;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 36px 44px;
    min-height: 240px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
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

# Compute metrics
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df["_month"] = df[date_col].dt.to_period("M")

total_revenue = df[revenue_col].sum()
total_profit  = df[profit_col].sum()
total_cost    = df[cost_col].sum()
total_orders  = len(df)
profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0
avg_order_val = df[revenue_col].mean()

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
# HIGH-DENSITY PLOTLY CHARTS (Dark Neon Palette)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Interactive Analytics Engine</div>', unsafe_allow_html=True)

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

ch1, ch2 = st.columns(2)

with ch1:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    fig1 = go.Figure()
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
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=monthly["Month_Label"], y=monthly["Revenue"],
        mode="lines+markers", name="Trend",
        line=dict(color="#38BDF8", width=3),
        marker=dict(size=7, color="#38BDF8"),
        fill="tozeroy", fillcolor="rgba(56, 189, 248, 0.08)",
    ))
    fig4.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(style_chart(fig4, "Revenue Velocity Curve (2024)"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SLIDE CAROUSEL PREVIEW (Interactive Deck Viewer)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Presentation Deck Preview (5 Slides)</div>', unsafe_allow_html=True)

if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0

slides = [
    {
        "num": "01", "name": "Executive Cover", "icon": "🏷️",
        "html": f'<div style="text-align:left;"><div style="font-size:12px;font-weight:700;color:#818CF8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:12px;">✦ AutoPilot Executive Report</div><h1 style="font-size:30px;font-weight:800;color:#F8FAFC;margin:0 0 12px 0;">{report_title}</h1><p style="font-size:14px;color:#94A3B8;margin:0;">Generated from {len(df):,} transactions · Confidential</p></div>'
    },
    {
        "num": "02", "name": "KPI Matrix", "icon": "📌",
        "html": f'<div style="display:grid;grid-template-columns:repeat(4, 1fr);gap:16px;"><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:16px;"><div style="font-size:10px;color:#64748B;font-weight:700;">REVENUE</div><div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-top:6px;">{fmt(total_revenue)}</div></div><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:16px;"><div style="font-size:10px;color:#64748B;font-weight:700;">PROFIT</div><div style="font-size:22px;font-weight:800;color:#34D399;margin-top:6px;">{fmt(total_profit)}</div></div><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:16px;"><div style="font-size:10px;color:#64748B;font-weight:700;">MARGIN</div><div style="font-size:22px;font-weight:800;color:#C084FC;margin-top:6px;">{profit_margin:.1f}%</div></div><div style="background:#0E131F;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:16px;"><div style="font-size:10px;color:#64748B;font-weight:700;">ORDERS</div><div style="font-size:22px;font-weight:800;color:#FBBF24;margin-top:6px;">{total_orders:,}</div></div></div>'
    },
    {
        "num": "03", "name": "Monthly Trajectory", "icon": "📈",
        "html": f'<div><div style="font-size:14px;font-weight:700;color:#818CF8;margin-bottom:8px;">Monthly Trajectory & Volatility</div><p style="font-size:14px;color:#94A3B8;line-height:1.6;">Peak revenue recorded in <strong>{best_month}</strong>. Lowest performance observed in <strong>{worst_month}</strong>.<br>Average month-over-month growth held at <strong>+{mom_avg:.1f}%</strong> across the evaluation cycle.</p></div>'
    },
    {
        "num": "04", "name": "Category Dominance", "icon": "🏆",
        "html": f'<div><div style="font-size:14px;font-weight:700;color:#818CF8;margin-bottom:8px;">Category & Product Mix</div><p style="font-size:14px;color:#94A3B8;line-height:1.6;"><strong>{top_cat}</strong> accounts for the largest share of net income.<br>Rebalancing supply and promotions around high-margin SKUs is recommended for upcoming quarters.</p></div>'
    },
    {
        "num": "05", "name": "Strategic Recommendations", "icon": "📍",
        "html": f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;"><div style="background:#0E131F;padding:14px;border-radius:8px;border-left:3px solid #6366F1;"><div style="font-size:11px;font-weight:700;color:#818CF8;">Market Focus</div><div style="font-size:13px;color:#94A3B8;margin-top:4px;">{top_region} is the primary revenue driver; expand distribution here.</div></div><div style="background:#0E131F;padding:14px;border-radius:8px;border-left:3px solid #34D399;"><div style="font-size:11px;font-weight:700;color:#34D399;">Seasonality Playbook</div><div style="font-size:13px;color:#94A3B8;margin-top:4px;">Schedule targeted promotions to mitigate the soft dip seen in {worst_month}.</div></div></div>'
    },
]

st.markdown('<div class="carousel-box">', unsafe_allow_html=True)
tab_cols = st.columns(len(slides))
for i, s in enumerate(slides):
    with tab_cols[i]:
        if st.button(f"{s['icon']} {s['name']}", key=f"s_{i}", use_container_width=True,
                     type="primary" if i == st.session_state.slide_idx else "secondary"):
            st.session_state.slide_idx = i
            st.rerun()

curr_s = slides[st.session_state.slide_idx]
st.markdown(f'<div class="slide-mockup"><div style="font-size:10px;font-weight:700;color:#64748B;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:16px;">Slide {curr_s["num"]} / 05 · {curr_s["name"]}</div>{curr_s["html"]}</div></div>', unsafe_allow_html=True)

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
    label="📥  Download Executive PowerPoint Deck (.pptx)",
    data=pptx_bytes,
    file_name=f"{safe_title}.pptx",
    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    use_container_width=True,
    type="primary",
)

st.caption("✦ Includes all generated charts, KPI summary cards, and speaker notes. Fully editable in PowerPoint & Google Slides.")

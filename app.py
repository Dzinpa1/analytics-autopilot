"""
app.py  —  Analytics AutoPilot
Streamlit web interface: upload CSV → interactive dashboard → download .pptx
Run with:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import io
import os
import tempfile

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Analytics AutoPilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #F8FAFC; }

    /* KPI Cards */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        border-left: 4px solid #2563EB;
        margin-bottom: 8px;
    }
    .kpi-label {
        font-size: 12px;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #1E293B;
        margin-top: 4px;
    }
    .kpi-sub {
        font-size: 12px;
        color: #94A3B8;
        margin-top: 2px;
    }

    /* Section headers */
    .section-header {
        font-size: 18px;
        font-weight: 700;
        color: #1E293B;
        margin: 24px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #E2E8F0;
    }

    /* Insight cards */
    .insight-card {
        background: white;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        margin-bottom: 10px;
    }
    .insight-title {
        font-size: 13px;
        font-weight: 700;
        color: #2563EB;
    }
    .insight-body {
        font-size: 13px;
        color: #334155;
        margin-top: 4px;
        line-height: 1.5;
    }

    /* Upload area styling */
    .uploadedFile { border-radius: 8px; }

    /* Hide default streamlit footer */
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_currency(val):
    if val >= 1_000_000:
        return f"${val/1_000_000:.2f}M"
    elif val >= 1_000:
        return f"${val/1_000:.1f}K"
    return f"${val:,.2f}"


def kpi_card(label, value, sub="", accent="#2563EB"):
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: {accent};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)


def insight_card(title, body):
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-title">{title}</div>
        <div class="insight-body">{body}</div>
    </div>""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/combo-chart.png", width=64)
    st.title("Analytics AutoPilot")
    st.caption("Turn raw data into executive-ready reports in seconds.")
    st.divider()

    st.subheader("⚙️ Settings")
    report_title = st.text_input("Report Title", value="2024 Sales Performance Report")
    brand_color  = st.color_picker("Brand Color", "#2563EB")

    st.divider()
    st.subheader("📋 How it works")
    st.markdown("""
    1. **Upload** your CSV or Excel file
    2. **Preview** auto-generated KPIs & charts
    3. **Download** your PowerPoint deck
    """)
    st.divider()
    st.caption("Analytics AutoPilot v0.1 — MVP")


# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown("## 📊 Analytics AutoPilot")
st.markdown("*Upload a dataset — get a full executive report in seconds.*")
st.divider()

# ── Upload section ────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Drop your CSV or Excel file here",
    type=["csv", "xlsx", "xls"],
    help="Supported formats: CSV, Excel (.xlsx, .xls)"
)

# ── Use sample data option ─────────────────────────────────────────────────────
use_sample = st.checkbox("🎲 Use auto-generated sample dataset instead", value=False)

if not uploaded_file and not use_sample:
    st.info("👆 Upload a file above, or check the box to use our sample retail sales dataset.")
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading data..."):
    if use_sample or uploaded_file is None:
        from generate_data import generate_sales_data
        df = generate_sales_data()
        st.success(f"✅ Sample dataset loaded — {df.shape[0]:,} rows × {df.shape[1]} columns")
    else:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.success(f"✅ **{uploaded_file.name}** loaded — {df.shape[0]:,} rows × {df.shape[1]} columns")

# ── Auto-detect columns ───────────────────────────────────────────────────────
st.markdown('<div class="section-header">🔍 Column Mapping</div>', unsafe_allow_html=True)

col_names = df.columns.tolist()

def find_col(candidates, cols):
    for c in candidates:
        for col in cols:
            if c.lower() in col.lower():
                return col
    return cols[0]

date_col    = find_col(["date", "time", "day", "month"],   col_names)
revenue_col = find_col(["revenue", "sales", "amount", "income", "total"], col_names)
profit_col  = find_col(["profit", "margin", "net"],        col_names)
cost_col    = find_col(["cost", "expense", "cogs"],        col_names)
cat_col     = find_col(["category", "type", "segment", "product_type"], col_names)

c1, c2, c3 = st.columns(3)
with c1:
    date_col    = st.selectbox("📅 Date column",    col_names, index=col_names.index(date_col))
    revenue_col = st.selectbox("💰 Revenue column", col_names, index=col_names.index(revenue_col))
with c2:
    profit_col  = st.selectbox("📈 Profit column",  col_names, index=col_names.index(profit_col))
    cost_col    = st.selectbox("💸 Cost column",    col_names, index=col_names.index(cost_col))
with c3:
    cat_col     = st.selectbox("🏷️ Category column", col_names, index=col_names.index(cat_col))
    region_cols = [c for c in col_names if any(x in c.lower() for x in ["region", "area", "zone", "location", "city"])]
    region_col  = st.selectbox("📍 Region column",  col_names, index=col_names.index(region_cols[0]) if region_cols else 0)

generate_btn = st.button("⚡ Generate Report", type="primary", use_container_width=True)

if not generate_btn:
    st.stop()

# ── Run analysis ──────────────────────────────────────────────────────────────
with st.spinner("🔬 Analysing data..."):
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["_month"] = df[date_col].dt.to_period("M")

    total_revenue  = df[revenue_col].sum()
    total_profit   = df[profit_col].sum()
    total_cost     = df[cost_col].sum()
    total_orders   = len(df)
    profit_margin  = (total_profit / total_revenue * 100) if total_revenue else 0
    avg_order_val  = df[revenue_col].mean()
    return_rate    = (df["Returned"].sum() / total_orders * 100) if "Returned" in df.columns else None

    monthly = (
        df.groupby("_month")
          .agg(**{
              "Revenue": (revenue_col, "sum"),
              "Profit":  (profit_col,  "sum"),
          })
          .reset_index()
    )
    monthly["Month_Label"] = monthly["_month"].dt.strftime("%b %Y")

    category = (
        df.groupby(cat_col)
          .agg(**{"Revenue": (revenue_col, "sum"), "Profit": (profit_col, "sum")})
          .reset_index()
          .sort_values("Revenue", ascending=False)
    )
    category["Margin_%"] = (category["Profit"] / category["Revenue"] * 100).round(1)

    region_df = (
        df.groupby(region_col)
          .agg(**{"Revenue": (revenue_col, "sum")})
          .reset_index()
          .sort_values("Revenue", ascending=False)
    )

    best_month  = monthly.loc[monthly["Revenue"].idxmax(), "Month_Label"]
    worst_month = monthly.loc[monthly["Revenue"].idxmin(), "Month_Label"]
    top_cat     = category.iloc[0][cat_col]
    top_region  = region_df.iloc[0][region_col]

# ── KPI Cards ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📌 Key Performance Indicators</div>', unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
with k1: kpi_card("Total Revenue",   fmt_currency(total_revenue),  "Full period",        brand_color)
with k2: kpi_card("Total Profit",    fmt_currency(total_profit),   "After costs",        "#10B981")
with k3: kpi_card("Profit Margin",   f"{profit_margin:.1f}%",      "Revenue to profit",  "#7C3AED")
with k4: kpi_card("Total Orders",    f"{total_orders:,}",          "Transactions",       "#F59E0B")

k5, k6, k7, k8 = st.columns(4)
with k5: kpi_card("Avg Order Value", fmt_currency(avg_order_val),  "Per transaction",    brand_color)
with k6: kpi_card("Best Month",      best_month,                   "Highest revenue",    "#10B981")
with k7: kpi_card("Top Category",    top_cat,                      "By revenue",         "#7C3AED")
with k8: kpi_card("Top Region",      top_region,                   "By revenue",         "#F59E0B")

# ── Charts ────────────────────────────────────────────────────────────────────
import plotly.graph_objects as go

PALETTE = [brand_color, "#7C3AED", "#10B981", "#F59E0B", "#EF4444",
           "#06B6D4", "#EC4899", "#84CC16", "#F97316", "#6366F1"]
BG   = "#F8FAFC"
TEXT = "#1E293B"

def clean_layout(fig, title):
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=TEXT), x=0.02),
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(family="Arial", color=TEXT),
        margin=dict(l=50, r=30, t=60, b=50),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(showgrid=False, linecolor="#CBD5E1")
    fig.update_yaxes(showgrid=True, gridcolor="#E2E8F0", linecolor="#CBD5E1")
    return fig

st.markdown('<div class="section-header">📈 Charts & Trends</div>', unsafe_allow_html=True)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # Monthly Revenue & Profit
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=monthly["Month_Label"], y=monthly["Revenue"],
                          name="Revenue", marker_color=brand_color, opacity=0.9))
    fig1.add_trace(go.Bar(x=monthly["Month_Label"], y=monthly["Profit"],
                          name="Profit", marker_color="#10B981", opacity=0.9))
    fig1.update_layout(barmode="group")
    clean_layout(fig1, "Monthly Revenue & Profit")
    fig1.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig1, use_container_width=True)

with chart_col2:
    # Category breakdown
    fig2 = go.Figure(go.Bar(
        x=category["Revenue"], y=category[cat_col],
        orientation="h",
        marker_color=PALETTE[:len(category)],
        text=[f"${v:,.0f}  ({m:.1f}%)" for v, m in zip(category["Revenue"], category["Margin_%"])],
        textposition="outside",
    ))
    clean_layout(fig2, f"Revenue by {cat_col}")
    fig2.update_xaxes(tickprefix="$", tickformat=",.0f")
    fig2.update_yaxes(autorange="reversed")
    st.plotly_chart(fig2, use_container_width=True)

chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    # Regional donut
    fig3 = go.Figure(go.Pie(
        labels=region_df[region_col], values=region_df["Revenue"],
        hole=0.45, marker=dict(colors=PALETTE[:len(region_df)],
        line=dict(color="white", width=2)),
        textinfo="label+percent",
    ))
    fig3.update_layout(
        title=dict(text=f"Revenue by {region_col}", font=dict(size=16, color=TEXT), x=0.02),
        paper_bgcolor=BG, font=dict(family="Arial", color=TEXT),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig3, use_container_width=True)

with chart_col4:
    # Monthly trend line
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=monthly["Month_Label"], y=monthly["Revenue"],
        mode="lines+markers",
        name="Revenue",
        line=dict(color=brand_color, width=3),
        marker=dict(size=8, color=brand_color),
        fill="tozeroy",
        fillcolor=f"rgba(37,99,235,0.08)"
    ))
    clean_layout(fig4, "Revenue Trend")
    fig4.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig4, use_container_width=True)

# ── AI Insights ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🧠 Executive Insights & Talking Points</div>', unsafe_allow_html=True)

ins1, ins2 = st.columns(2)
with ins1:
    insight_card("📈 Peak Performance",
                 f"Your strongest month was <strong>{best_month}</strong>, which should guide your inventory and marketing calendar for next year.")
    insight_card("🏆 Top Category",
                 f"<strong>{top_cat}</strong> generated the highest revenue. Consider expanding the product range in this category to capture more market share.")
    insight_card("📍 Regional Opportunity",
                 f"<strong>{top_region}</strong> leads all regions in revenue. Use this as a base for your next product launch or promotional campaign.")

with ins2:
    insight_card("⚠️ Low Period",
                 f"<strong>{worst_month}</strong> was your softest month. Investigate whether this is seasonal or operational, and plan targeted promotions early.")
    insight_card("💰 Margin Health",
                 f"At <strong>{profit_margin:.1f}%</strong>, your profit margin is {'healthy ✅' if profit_margin > 35 else 'below target — review cost structure ⚠️'}.")
    insight_card("🛒 Order Value",
                 f"Average order value is <strong>{fmt_currency(avg_order_val)}</strong>. Consider upsell/bundle strategies to push this higher.")

# ── Data preview ──────────────────────────────────────────────────────────────
with st.expander("🔎 Raw Data Preview (first 50 rows)"):
    st.dataframe(df.head(50), use_container_width=True)

# ── Export: PowerPoint ────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📥 Export</div>', unsafe_allow_html=True)

with st.spinner("🔧 Building your PowerPoint deck..."):
    # Save temp CSV for the pipeline to consume
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
        df.to_csv(tmp.name, index=False)
        tmp_csv_path = tmp.name

    # Build report dict on the fly from already-computed data
    monthly_export = monthly.copy()
    monthly_export["MoM_Growth"] = monthly_export["Revenue"].pct_change() * 100

    if "Product" in df.columns:
        top_products = (
            df.groupby("Product")
              .agg(Revenue=(revenue_col, "sum"), Quantity=("Quantity", "sum"))
              .reset_index()
              .sort_values("Revenue", ascending=False)
              .head(5)
        )
    else:
        top_products = category.rename(columns={cat_col: "Product"}).head(5)
        top_products["Quantity"] = 0

    report_data = {
        "kpis": {
            "total_revenue":   round(total_revenue,  2),
            "total_profit":    round(total_profit,   2),
            "total_cost":      round(total_cost,     2),
            "total_orders":    total_orders,
            "total_units":     int(df["Quantity"].sum()) if "Quantity" in df.columns else 0,
            "avg_order_value": round(avg_order_val,  2),
            "profit_margin":   round(profit_margin,  2),
            "return_rate":     round(return_rate, 2) if return_rate else 0,
        },
        "monthly":      monthly_export,
        "category":     category,
        "region":       region_df.rename(columns={region_col: "Region"}),
        "top_products": top_products,
        "channels":     pd.DataFrame({"Channel": ["N/A"], "Revenue": [0], "Orders": [0], "Revenue_%": [100]}),
        "insights": {
            "best_month":     best_month,
            "worst_month":    worst_month,
            "avg_mom_growth": 0,
            "top_category":   top_cat,
            "top_region":     top_region,
            "top_channel":    "N/A",
        }
    }

    # Generate charts to temp files
    import tempfile as tf2
    tmp_output = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(tmp_output, exist_ok=True)

    from chart_engine import generate_all_charts
    chart_paths = generate_all_charts(report_data)

    # Build the deck
    from slide_builder import build_presentation
    pptx_path = build_presentation(report_data, chart_paths)

    # Read pptx into memory for download button
    with open(pptx_path, "rb") as f:
        pptx_bytes = f.read()

safe_title = report_title.replace(" ", "_")
st.download_button(
    label="📥 Download PowerPoint Presentation (.pptx)",
    data=pptx_bytes,
    file_name=f"{safe_title}.pptx",
    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    use_container_width=True,
    type="primary",
)

st.caption("💡 The downloaded .pptx is fully editable in Microsoft PowerPoint or Google Slides.")

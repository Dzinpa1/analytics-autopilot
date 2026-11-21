"""
chart_engine.py
Generates 4 publication-quality charts using Plotly (pure Python wheels,
works on Python 3.15). Exports PNG via kaleido if available, otherwise
falls back to saving interactive HTML previews.
"""

import os
import pandas as pd

# ── Brand palette ─────────────────────────────────────────────────────────────
PRIMARY   = "#2563EB"
SECONDARY = "#7C3AED"
ACCENT    = "#10B981"
WARN      = "#F59E0B"
DANGER    = "#EF4444"
BG        = "#F8FAFC"
TEXT      = "#1E293B"
PALETTE   = [PRIMARY, SECONDARY, ACCENT, WARN, DANGER,
             "#06B6D4", "#EC4899", "#84CC16", "#F97316", "#6366F1"]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def _try_import_plotly():
    import plotly.graph_objects as go
    import plotly.express as px
    return go, px


def _save_fig(fig, name: str) -> str:
    """Try PNG via kaleido; fall back to HTML."""
    path_png  = os.path.join(OUTPUT_DIR, name)
    path_html = path_png.replace(".png", ".html")
    try:
        fig.write_image(path_png, width=1100, height=550, scale=1.5)
        print(f"  ✅  Saved PNG : {name}")
        return path_png
    except Exception:
        fig.write_html(path_html)
        print(f"  ⚠️   kaleido not available — saved HTML: {name.replace('.png','.html')}")
        return path_html


def _layout(fig, title: str):
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=TEXT), x=0.04),
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(family="Arial, sans-serif", color=TEXT),
        margin=dict(l=60, r=40, t=70, b=60),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
    )
    fig.update_xaxes(showgrid=False, linecolor="#CBD5E1")
    fig.update_yaxes(showgrid=True,  gridcolor="#E2E8F0", linecolor="#CBD5E1")
    return fig


# ── Chart 1: Monthly Revenue & Profit (grouped bar) ───────────────────────────
def chart_monthly_trend(monthly: pd.DataFrame) -> str:
    go, px = _try_import_plotly()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly["Month_Label"], y=monthly["Revenue"],
        name="Revenue", marker_color=PRIMARY, opacity=0.9,
        text=[f"${v:,.0f}" for v in monthly["Revenue"]],
        textposition="outside", textfont=dict(size=9),
    ))
    fig.add_trace(go.Bar(
        x=monthly["Month_Label"], y=monthly["Profit"],
        name="Profit", marker_color=ACCENT, opacity=0.9,
    ))
    fig.update_layout(barmode="group")
    _layout(fig, "Monthly Revenue & Profit (2024)")
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    return _save_fig(fig, "chart_monthly_trend.png")


# ── Chart 2: Revenue by Category (horizontal bar) ─────────────────────────────
def chart_category(category: pd.DataFrame) -> str:
    go, px = _try_import_plotly()
    fig = go.Figure(go.Bar(
        x=category["Revenue"],
        y=category["Category"],
        orientation="h",
        marker_color=PALETTE[:len(category)],
        text=[f"${v:,.0f}  ({m:.1f}% margin)"
              for v, m in zip(category["Revenue"], category["Margin_%"])],
        textposition="outside",
        textfont=dict(size=10),
    ))
    _layout(fig, "Revenue by Category (with Profit Margin %)")
    fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    fig.update_yaxes(autorange="reversed")
    return _save_fig(fig, "chart_category.png")


# ── Chart 3: Revenue by Region (donut) ────────────────────────────────────────
def chart_region(region: pd.DataFrame) -> str:
    go, px = _try_import_plotly()
    fig = go.Figure(go.Pie(
        labels=region["Region"],
        values=region["Revenue"],
        hole=0.45,
        marker=dict(colors=PALETTE[:len(region)],
                    line=dict(color="white", width=2)),
        textinfo="label+percent",
        textfont=dict(size=12),
    ))
    fig.update_layout(
        title=dict(text="Revenue Share by Region", font=dict(size=18, color=TEXT), x=0.04),
        paper_bgcolor=BG,
        font=dict(family="Arial, sans-serif", color=TEXT),
        margin=dict(l=40, r=40, t=70, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        showlegend=True,
    )
    return _save_fig(fig, "chart_region.png")


# ── Chart 4: Top 5 Products (vertical bar) ────────────────────────────────────
def chart_top_products(top_products: pd.DataFrame) -> str:
    go, px = _try_import_plotly()
    fig = go.Figure(go.Bar(
        x=top_products["Product"],
        y=top_products["Revenue"],
        marker_color=PALETTE[:len(top_products)],
        text=[f"${v:,.0f}<br>{q:,} units"
              for v, q in zip(top_products["Revenue"], top_products["Quantity"])],
        textposition="outside",
        textfont=dict(size=10),
    ))
    _layout(fig, "Top 5 Products by Revenue")
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    return _save_fig(fig, "chart_top_products.png")


def generate_all_charts(report_data: dict) -> dict:
    print("\n📊  Generating charts...")
    paths = {
        "monthly_trend": chart_monthly_trend(report_data["monthly"]),
        "category":      chart_category(report_data["category"]),
        "region":        chart_region(report_data["region"]),
        "top_products":  chart_top_products(report_data["top_products"]),
    }
    print("  All charts saved to /output\n")
    return paths


if __name__ == "__main__":
    from analysis_engine import build_report
    path   = os.path.join(os.path.dirname(__file__), "sales_data.csv")
    report = build_report(path)
    generate_all_charts(report)


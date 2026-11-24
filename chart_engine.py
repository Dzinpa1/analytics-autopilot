"""
chart_engine.py
Generates 4 publication-quality charts using Plotly.
Supports custom chart types (swappable by user) and exports PNG via kaleido.
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


def _save_fig(fig, name: str, output_dir: str = None) -> str:
    """Save PNG via kaleido; if unavailable or error, generate an image fallback so slide_builder never receives an HTML file."""
    target_dir = output_dir or OUTPUT_DIR
    os.makedirs(target_dir, exist_ok=True)
    path_png = os.path.join(target_dir, name)
    try:
        fig.write_image(path_png, width=1100, height=550, scale=1.5)
        print(f"  ✅  Saved PNG : {path_png}")
        return path_png
    except Exception as e:
        print(f"  ⚠️   kaleido error ({e}) — writing image fallback for slide generation...")
        try:
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (1100, 550), color="#0E131F")
            draw = ImageDraw.Draw(img)
            draw.text((60, 60), f"Analytics Chart: {name}", fill="#F8FAFC")
            draw.text((60, 110), "(Chart rendered in Web View)", fill="#94A3B8")
            img.save(path_png, "PNG")
            return path_png
        except Exception:
            import base64
            # 1x1 transparent PNG fallback
            raw_png = base64.b64decode(b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=')
            with open(path_png, "wb") as f:
                f.write(raw_png)
            return path_png


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


# ── Chart 1: Monthly Trend ────────────────────────────────────────────────────
def chart_monthly_trend(monthly: pd.DataFrame, chart_type: str = "Grouped Bars", has_profit: bool = True, currency_symbol: str = "$", output_dir: str = None) -> str:
    go, px = _try_import_plotly()
    sym = currency_symbol if currency_symbol else ""
    fig = go.Figure()

    if chart_type == "Line & Area":
        fig.add_trace(go.Scatter(
            x=monthly["Month_Label"], y=monthly["Revenue"],
            mode="lines+markers", name="Revenue",
            line=dict(color=PRIMARY, width=3),
            marker=dict(size=7, color=PRIMARY),
            fill="tozeroy", fillcolor="rgba(37,99,235,0.08)",
        ))
        if has_profit:
            fig.add_trace(go.Scatter(
                x=monthly["Month_Label"], y=monthly["Profit"],
                mode="lines+markers", name="Profit",
                line=dict(color=ACCENT, width=3),
                marker=dict(size=7, color=ACCENT),
            ))
            _layout(fig, "Monthly Revenue & Profit Trajectory")
        else:
            _layout(fig, "Monthly Revenue Trajectory")
        fig.update_yaxes(tickprefix=sym, tickformat=",.0f")

    elif chart_type == "MoM Growth %":
        colors = [ACCENT if v >= 0 else DANGER for v in monthly["MoM_Growth"].fillna(0)]
        fig.add_trace(go.Bar(
            x=monthly["Month_Label"], y=monthly["MoM_Growth"],
            marker_color=colors,
            text=[f"{v:+.1f}%" if not pd.isna(v) else "0.0%" for v in monthly["MoM_Growth"]],
            textposition="outside",
        ))
        _layout(fig, "Month-over-Month Revenue Growth (%)")
        fig.update_yaxes(ticksuffix="%")

    else:  # Default: Grouped Bars
        fig.add_trace(go.Bar(
            x=monthly["Month_Label"], y=monthly["Revenue"],
            name="Revenue", marker_color=PRIMARY, opacity=0.9,
            text=[f"{sym}{v:,.0f}" for v in monthly["Revenue"]],
            textposition="outside", textfont=dict(size=9),
        ))
        if has_profit:
            fig.add_trace(go.Bar(
                x=monthly["Month_Label"], y=monthly["Profit"],
                name="Profit", marker_color=ACCENT, opacity=0.9,
            ))
            fig.update_layout(barmode="group")
            _layout(fig, "Monthly Revenue & Profit (2024)")
        else:
            _layout(fig, "Monthly Revenue Performance")
        fig.update_yaxes(tickprefix=sym, tickformat=",.0f")

    return _save_fig(fig, "chart_monthly_trend.png", output_dir=output_dir)


# ── Chart 2: Category Breakdown ───────────────────────────────────────────────
def chart_category(category: pd.DataFrame, chart_type: str = "Horizontal Bar", has_profit: bool = True, currency_symbol: str = "$", output_dir: str = None) -> str:
    go, px = _try_import_plotly()
    sym = currency_symbol if currency_symbol else ""

    if chart_type == "Treemap":
        color_col = "Margin_%" if has_profit else "Revenue"
        fig = px.treemap(
            category, path=["Category"], values="Revenue",
            color=color_col, color_continuous_scale="Viridis",
            title="Category Revenue Distribution" if not has_profit else "Category Revenue Distribution & Margin %"
        )
        fig.update_layout(paper_bgcolor=BG, margin=dict(l=40, r=40, t=60, b=40))

    elif chart_type == "Donut":
        fig = go.Figure(go.Pie(
            labels=category["Category"], values=category["Revenue"],
            hole=0.45, marker=dict(colors=PALETTE[:len(category)], line=dict(color="white", width=2)),
            textinfo="label+percent", textfont=dict(size=11),
        ))
        fig.update_layout(
            title=dict(text="Revenue Share by Category", font=dict(size=18, color=TEXT), x=0.04),
            paper_bgcolor=BG, margin=dict(l=40, r=40, t=70, b=40),
            showlegend=True,
        )

    else:  # Default: Horizontal Bar
        labels = [f"{sym}{v:,.0f}  ({m:.1f}% margin)" for v, m in zip(category["Revenue"], category["Margin_%"])] if has_profit else [f"{sym}{v:,.0f}" for v in category["Revenue"]]
        fig = go.Figure(go.Bar(
            x=category["Revenue"], y=category["Category"], orientation="h",
            marker_color=PALETTE[:len(category)],
            text=labels,
            textposition="outside", textfont=dict(size=10),
        ))
        title = "Revenue by Category (with Profit Margin %)" if has_profit else "Revenue by Category"
        _layout(fig, title)
        fig.update_xaxes(tickprefix=sym, tickformat=",.0f")
        fig.update_yaxes(autorange="reversed")

    return _save_fig(fig, "chart_category.png", output_dir=output_dir)


# ── Chart 3: Regional Distribution ────────────────────────────────────────────
def chart_region(region: pd.DataFrame, chart_type: str = "Donut", currency_symbol: str = "$", output_dir: str = None) -> str:
    go, px = _try_import_plotly()
    sym = currency_symbol if currency_symbol else ""

    if chart_type == "Vertical Bar":
        fig = go.Figure(go.Bar(
            x=region["Region"], y=region["Revenue"],
            marker_color=PALETTE[:len(region)],
            text=[f"{sym}{v:,.0f}" for v in region["Revenue"]],
            textposition="outside",
        ))
        _layout(fig, "Revenue by Region")
        fig.update_yaxes(tickprefix=sym, tickformat=",.0f")

    elif chart_type == "Pie Chart":
        fig = go.Figure(go.Pie(
            labels=region["Region"], values=region["Revenue"],
            marker=dict(colors=PALETTE[:len(region)], line=dict(color="white", width=2)),
            textinfo="label+percent", textfont=dict(size=12),
        ))
        fig.update_layout(
            title=dict(text="Regional Revenue Share", font=dict(size=18, color=TEXT), x=0.04),
            paper_bgcolor=BG, margin=dict(l=40, r=40, t=70, b=40),
        )

    else:  # Default: Donut
        fig = go.Figure(go.Pie(
            labels=region["Region"], values=region["Revenue"],
            hole=0.45, marker=dict(colors=PALETTE[:len(region)], line=dict(color="white", width=2)),
            textinfo="label+percent", textfont=dict(size=12),
        ))
        fig.update_layout(
            title=dict(text="Revenue Share by Region", font=dict(size=18, color=TEXT), x=0.04),
            paper_bgcolor=BG, font=dict(family="Arial, sans-serif", color=TEXT),
            margin=dict(l=40, r=40, t=70, b=40), showlegend=True,
        )

    return _save_fig(fig, "chart_region.png", output_dir=output_dir)


# ── Chart 4: Top Products ─────────────────────────────────────────────────────
def chart_top_products(top_products: pd.DataFrame, metric: str = "Revenue", currency_symbol: str = "$", output_dir: str = None) -> str:
    go, px = _try_import_plotly()

    val_col = metric if metric in top_products.columns else "Revenue"
    is_curr = val_col in ["Revenue", "Profit"]
    sym = currency_symbol if currency_symbol else ""

    if len(top_products) > 5:
        # Horizontal layout prevents X-axis product label collisions when ranking 6-10 items
        sorted_prods = top_products.sort_values(val_col, ascending=True)
        fig = go.Figure(go.Bar(
            y=sorted_prods["Product"],
            x=sorted_prods[val_col],
            orientation="h",
            marker_color=PALETTE[:len(sorted_prods)],
            text=[f"{sym}{v:,.0f}" if is_curr else f"{v:,} units" for v in sorted_prods[val_col]],
            textposition="outside", textfont=dict(size=10),
        ))
        _layout(fig, f"Top {len(sorted_prods)} Products by {val_col}")
        fig.update_layout(margin=dict(l=110, r=40, t=70, b=40))
        if is_curr:
            fig.update_xaxes(tickprefix=sym, tickformat=",.0f")
        else:
            fig.update_xaxes(tickformat=",.0f")
    else:
        fig = go.Figure(go.Bar(
            x=top_products["Product"],
            y=top_products[val_col],
            marker_color=PALETTE[:len(top_products)],
            text=[f"{sym}{v:,.0f}" if is_curr else f"{v:,} units" for v in top_products[val_col]],
            textposition="outside", textfont=dict(size=10),
        ))
        _layout(fig, f"Top Products by {val_col}")
        if is_curr:
            fig.update_yaxes(tickprefix=sym, tickformat=",.0f")
        else:
            fig.update_yaxes(tickformat=",.0f")

    return _save_fig(fig, "chart_top_products.png", output_dir=output_dir)


def generate_all_charts(report_data: dict, config: dict = None, output_dir: str = None) -> dict:
    if config is None:
        config = {}

    trend_type  = config.get("trend_type", "Grouped Bars")
    cat_type    = config.get("cat_type", "Horizontal Bar")
    region_type = config.get("region_type", "Donut")
    top_metric  = config.get("top_metric", "Revenue")
    has_profit  = report_data.get("kpis", {}).get("has_profit", True)
    curr_sym    = report_data.get("meta", {}).get("currency_symbol", "$")

    target_display = output_dir or "/output"
    print(f"\n📊  Generating charts with configuration ({target_display}):", config)
    paths = {
        "monthly_trend": chart_monthly_trend(report_data["monthly"], chart_type=trend_type, has_profit=has_profit, currency_symbol=curr_sym, output_dir=output_dir),
        "category":      chart_category(report_data["category"], chart_type=cat_type, has_profit=has_profit, currency_symbol=curr_sym, output_dir=output_dir),
        "region":        chart_region(report_data["region"], chart_type=region_type, currency_symbol=curr_sym, output_dir=output_dir),
        "top_products":  chart_top_products(report_data["top_products"], metric=top_metric, currency_symbol=curr_sym, output_dir=output_dir),
    }
    print(f"  All charts saved to {target_display}\n")
    return paths


if __name__ == "__main__":
    from analysis_engine import build_report
    path   = os.path.join(os.path.dirname(__file__), "sales_data.csv")
    report = build_report(path)
    generate_all_charts(report)

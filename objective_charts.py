"""Turn a Finding's chart spec + table into a styled Plotly figure (used by the app and slide deck)."""
from typing import Optional
import pandas as pd

import analyses as an

PALETTE = ["#6366F1", "#38BDF8", "#818CF8", "#0EA5E9", "#A5B4FC", "#34D399"]
DARK_PANEL_BG = "#111827"
GRID_COLOR = "#1F2937"
DANGER_COLOR = "#F87171"
SUCCESS_COLOR = "#34D399"


def _clean_period_labels(labels: pd.Series) -> pd.Series:
    """Compact 'Jan 2026', 'Feb 2026' -> 'Jan', 'Feb' when all dates share a single year."""
    s = labels.astype(str)
    parts = s.str.extract(r"^([A-Za-z]{3})\s+(\d{4})$")
    if parts[0].notna().all() and parts[1].nunique() == 1:
        return parts[0]
    return s


def _auto_tickangle(labels: pd.Series, kind: str) -> int:
    """Angle x-axis labels only when labels are long or numerous."""
    if kind in ("Donut", "Pie", "Horizontal Bar", "scatter", "hist") or labels.empty:
        return 0
    strs = labels.astype(str).tolist()
    n = len(strs)
    max_len = max((len(s) for s in strs), default=0)
    if n > 12 or (n >= 4 and max_len > 10) or max_len > 14:
        return -25
    return 0


def _is_pct_col(col: str) -> bool:
    s = str(col).lower()
    return "%" in s or "pct" in s or "share" in s or "margin" in s or "growth" in s


def _fmt_label(val, money: bool, pct: bool, currency: str) -> str:
    if val is None or pd.isna(val):
        return ""
    if pct:
        return f"{val:.1f}%"
    return an.fmt(float(val), money=money, sym=currency)


def figure_for(
    finding,
    dark: bool = True,
    width_hint: int = 0,
    brand_color: Optional[str] = None,
    tickangle: Optional[int] = None,
    chart_style: Optional[str] = None,
    currency: str = "",
    top_n: Optional[int] = None,
) -> Optional[object]:
    """Return a Neon Obsidian styled plotly Figure or None when the finding has no drawable chart."""
    spec, tbl = finding.chart, finding.table
    if not spec or tbl is None or not isinstance(tbl, pd.DataFrame) or tbl.empty:
        return None
    import plotly.graph_objects as go

    x, y, base_kind = spec.get("x"), spec.get("y"), spec.get("type")
    if x not in tbl.columns:
        return None
    if base_kind != "hist" and y not in tbl.columns:
        return None

    df_plot = tbl.copy()
    if top_n is not None and top_n > 0 and base_kind == "bar" and len(df_plot) > top_n:
        df_plot = df_plot.head(top_n)

    style = chart_style
    if not style:
        style = {"line": "Line & Area", "bar": "Vertical Bar", "scatter": "scatter", "hist": "hist"}.get(base_kind, base_kind)

    primary = brand_color if (brand_color and str(brand_color).startswith("#")) else PALETTE[0]
    palette = [primary] + [c for c in PALETTE if c.lower() != primary.lower()]
    fg = "#94A3B8" if dark else "#1E293B"
    grid_c = GRID_COLOR if dark else "#E2E8F0"
    dark_bg = DARK_PANEL_BG if dark else "#FFFFFF"
    paper_bg = DARK_PANEL_BG if dark else "#FFFFFF"
    font_family = "Plus Jakarta Sans, -apple-system, sans-serif" if dark else "Arial, sans-serif"

    x_series = _clean_period_labels(df_plot[x]) if base_kind == "line" else df_plot[x].astype(str)
    y_name = str(y) if y else ""
    pct_y = _is_pct_col(y_name)
    money_y = an.is_money(y_name) and not pct_y and an.is_money(getattr(finding, "question", "") + " " + y_name)
    if not money_y and not pct_y:
        money_y = an.is_money(y_name)

    fig = go.Figure()

    if style in ("Donut", "Pie") and base_kind != "hist":
        vals = pd.to_numeric(df_plot[y], errors="coerce").fillna(0)
        if (vals < 0).any() or float(vals.sum()) <= 0:
            style = "Vertical Bar"
        else:
            pie_df = pd.DataFrame({"_lbl": x_series, "_val": vals}).sort_values("_val", ascending=False)
            if len(pie_df) > 6:
                other_sum = float(pie_df.iloc[5:]["_val"].sum())
                pie_df = pd.concat([pie_df.iloc[:5], pd.DataFrame([{"_lbl": "Other", "_val": other_sum}])], ignore_index=True)
            hole = 0.55 if style == "Donut" else 0.0
            fig.add_trace(go.Pie(
                labels=pie_df["_lbl"],
                values=pie_df["_val"],
                hole=hole,
                marker=dict(colors=[palette[i % len(palette)] for i in range(len(pie_df))], line=dict(color=dark_bg, width=2)),
                textinfo="label+percent",
                textposition="inside",
                insidetextorientation="horizontal",
                textfont=dict(color="#F8FAFC" if dark else "#1E293B", size=10.5),
            ))
            fig.update_layout(
                paper_bgcolor=paper_bg,
                font=dict(family=font_family, color=fg),
                margin=dict(l=20, r=20, t=16, b=20),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=fg)),
                showlegend=True,
            )
            return fig

    if style in ("Line & Area", "line") and base_kind != "hist":
        vals = pd.to_numeric(df_plot[y], errors="coerce")
        fig.add_trace(go.Scatter(
            x=x_series,
            y=vals,
            mode="lines+markers",
            name=y_name,
            line=dict(color=primary, width=3),
            marker=dict(size=7, color=primary),
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.12)" if primary == PALETTE[0] else "rgba(56, 189, 248, 0.12)",
        ))
    elif style == "Growth %" and base_kind != "hist":
        vals = pd.to_numeric(df_plot[y], errors="coerce")
        pct_change = vals.pct_change() * 100.0
        g_vals = pct_change.fillna(0.0)
        g_colors = [SUCCESS_COLOR if v >= 0 else DANGER_COLOR for v in g_vals]
        fig.add_trace(go.Bar(
            x=x_series,
            y=g_vals,
            marker_color=g_colors,
            text=[f"{v:+.1f}%" if not pd.isna(pct_change.iloc[i]) else "" for i, v in enumerate(g_vals)],
            textposition="outside",
            textfont=dict(color=fg, size=10),
        ))
        pct_y, money_y = True, False
    elif style == "Horizontal Bar" and base_kind != "hist":
        vals = pd.to_numeric(df_plot[y], errors="coerce")
        colors = [palette[i % len(palette)] if (pd.notna(v) and v >= 0) else DANGER_COLOR for i, v in enumerate(vals)]
        labels = [_fmt_label(v, money_y, pct_y, currency) for v in vals]
        fig.add_trace(go.Bar(
            x=vals,
            y=x_series,
            orientation="h",
            marker_color=colors,
            opacity=0.92,
            text=labels,
            textposition="outside",
            textfont=dict(color=fg, size=10.5),
            cliponaxis=False,
        ))
    elif style in ("Vertical Bar", "Grouped Bars", "bar") and base_kind in ("bar", "line"):
        vals = pd.to_numeric(df_plot[y], errors="coerce")
        is_series = (base_kind == "line")
        colors = [primary if (pd.notna(v) and v >= 0) else DANGER_COLOR for v in vals] if is_series else [palette[i % len(palette)] if (pd.notna(v) and v >= 0) else DANGER_COLOR for i, v in enumerate(vals)]
        show_txt = (not is_series) and (len(vals) <= 10)
        labels = [_fmt_label(v, money_y, pct_y, currency) for v in vals] if show_txt else None
        fig.add_trace(go.Bar(
            x=x_series,
            y=vals,
            marker_color=colors,
            opacity=0.92,
            text=labels,
            textposition="outside" if labels else None,
            textfont=dict(color=fg, size=10),
            cliponaxis=False,
        ))
    elif style == "scatter" or base_kind == "scatter":
        fig.add_trace(go.Scatter(
            x=df_plot[x],
            y=df_plot[y],
            mode="markers",
            marker=dict(color=primary, opacity=0.68, size=7, line=dict(width=0.5, color="#F8FAFC")),
        ))
    elif style == "hist" or base_kind == "hist":
        fig.add_trace(go.Histogram(
            x=pd.to_numeric(df_plot[x], errors="coerce").dropna(),
            marker_color=primary,
            opacity=0.88,
        ))
    else:
        return None

    angle = tickangle if tickangle is not None else _auto_tickangle(x_series, style)
    bot_margin = 55 if angle != 0 else 36
    top_margin = 24 if style in ("Vertical Bar", "Grouped Bars", "Growth %", "Horizontal Bar") else 16

    if style == "Horizontal Bar":
        fig.update_layout(
            paper_bgcolor=paper_bg,
            plot_bgcolor=paper_bg,
            font=dict(family=font_family, color=fg),
            margin=dict(l=40, r=55, t=top_margin, b=36),
            showlegend=False,
        )
        fig.update_yaxes(autorange="reversed", showgrid=False, linecolor=grid_c)
        x_tick = dict(showgrid=True, gridcolor=grid_c, linecolor=grid_c)
        if money_y and currency:
            x_tick.update(tickprefix=currency, tickformat=",.0f")
        elif pct_y:
            x_tick.update(ticksuffix="%")
        fig.update_xaxes(**x_tick)
    else:
        fig.update_layout(
            paper_bgcolor=paper_bg,
            plot_bgcolor=paper_bg,
            font=dict(family=font_family, color=fg),
            margin=dict(l=40, r=20, t=top_margin, b=bot_margin),
            showlegend=False,
        )
        fig.update_xaxes(showgrid=False, linecolor=grid_c, tickcolor=grid_c, tickangle=angle)
        y_tick = dict(showgrid=True, gridcolor=grid_c, linecolor=grid_c)
        if money_y and currency and base_kind != "hist":
            y_tick.update(tickprefix=currency, tickformat=",.0f")
        elif pct_y:
            y_tick.update(ticksuffix="%")
        fig.update_yaxes(**y_tick)
    return fig

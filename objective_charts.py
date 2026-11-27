"""Turn a Finding's chart spec + table into a Plotly figure (used by the app and the slide deck)."""
from typing import Optional
import pandas as pd

PALETTE = ["#6366F1", "#38BDF8", "#818CF8", "#0EA5E9", "#A5B4FC", "#64748B"]
DANGER_COLOR = "#EF4444"


def _auto_tickangle(labels: pd.Series, kind: str) -> int:
    """Angle x-axis labels when categories are long or numerous so labels never collide."""
    if kind not in ("bar", "line") or labels.empty:
        return 0
    strs = labels.astype(str).tolist()
    n = len(strs)
    max_len = max((len(s) for s in strs), default=0)
    if n > 10 or (n >= 4 and max_len > 10) or max_len > 14:
        return -25
    return 0


def figure_for(
    finding,
    dark: bool = True,
    width_hint: int = 0,
    brand_color: Optional[str] = None,
    tickangle: Optional[int] = None,
) -> Optional[object]:
    """Return a styled plotly Figure or None when the finding has no drawable chart."""
    spec, tbl = finding.chart, finding.table
    if not spec or tbl is None or not isinstance(tbl, pd.DataFrame) or tbl.empty:
        return None
    import plotly.graph_objects as go

    x, y, kind = spec.get("x"), spec.get("y"), spec.get("type")
    if x not in tbl.columns:
        return None
    if kind != "hist" and y not in tbl.columns:
        return None

    primary = brand_color or PALETTE[0]
    fg = "#94A3B8" if dark else "#1E293B"
    grid_c = "#1F2937" if dark else "#E2E8F0"
    bg = "rgba(0,0,0,0)" if dark else "#FFFFFF"
    font_family = "Plus Jakarta Sans, -apple-system, sans-serif" if dark else "Arial, sans-serif"

    fig = go.Figure()
    if kind == "line":
        fig.add_trace(go.Scatter(
            x=tbl[x].astype(str),
            y=tbl[y],
            mode="lines+markers",
            line=dict(color=primary, width=3),
            marker=dict(size=6, color=primary),
        ))
    elif kind == "bar":
        vals = pd.to_numeric(tbl[y], errors="coerce")
        colors = [primary if (v is not None and pd.notna(v) and v >= 0) else DANGER_COLOR for v in vals]
        fig.add_trace(go.Bar(
            x=tbl[x].astype(str),
            y=vals,
            marker_color=colors,
            opacity=0.92,
        ))
    elif kind == "scatter":
        fig.add_trace(go.Scatter(
            x=tbl[x],
            y=tbl[y],
            mode="markers",
            marker=dict(color=primary, opacity=0.65, size=7),
        ))
    elif kind == "hist":
        fig.add_trace(go.Histogram(
            x=pd.to_numeric(tbl[x], errors="coerce").dropna(),
            marker_color=primary,
            opacity=0.88,
        ))
    else:
        return None

    angle = tickangle if tickangle is not None else _auto_tickangle(tbl[x], kind)
    bot_margin = 55 if angle != 0 else 40

    fig.update_layout(
        paper_bgcolor=bg,
        plot_bgcolor=bg,
        font=dict(family=font_family, color=fg),
        margin=dict(l=45, r=20, t=24, b=bot_margin),
        showlegend=False,
        xaxis_title=str(x),
        yaxis_title=str(y) if kind != "hist" else "Count",
    )
    fig.update_xaxes(showgrid=False, linecolor=grid_c, tickcolor=grid_c, tickangle=angle)
    fig.update_yaxes(showgrid=True, gridcolor=grid_c, linecolor=grid_c)
    return fig

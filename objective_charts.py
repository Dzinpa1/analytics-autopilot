"""Turn a Finding's chart spec + table into a Plotly figure (used by the app and the slide deck)."""
from typing import Optional
import pandas as pd

PALETTE = ["#6366F1", "#10B981", "#F59E0B", "#EF4444", "#0EA5E9", "#8B5CF6"]


def figure_for(finding, dark: bool = True, width_hint: int = 0) -> Optional[object]:
    """Return a plotly Figure or None when the finding has no drawable chart."""
    spec, tbl = finding.chart, finding.table
    if not spec or tbl is None or not isinstance(tbl, pd.DataFrame) or tbl.empty:
        return None
    import plotly.graph_objects as go
    x, y, kind = spec.get("x"), spec.get("y"), spec.get("type")
    if x not in tbl.columns:
        return None
    if kind != "hist" and y not in tbl.columns:
        return None
    fg = "#E2E8F0" if dark else "#1E293B"
    fig = go.Figure()
    if kind == "line":
        fig.add_trace(go.Scatter(x=tbl[x].astype(str), y=tbl[y], mode="lines+markers", line=dict(color=PALETTE[0], width=3)))
    elif kind == "bar":
        vals = pd.to_numeric(tbl[y], errors="coerce")
        colors = [PALETTE[1] if (v is not None and v >= 0) else PALETTE[3] for v in vals]
        fig.add_trace(go.Bar(x=tbl[x].astype(str), y=vals, marker_color=colors))
    elif kind == "scatter":
        fig.add_trace(go.Scatter(x=tbl[x], y=tbl[y], mode="markers", marker=dict(color=PALETTE[0], opacity=0.6)))
    elif kind == "hist":
        fig.add_trace(go.Histogram(x=pd.to_numeric(tbl[x], errors="coerce").dropna(), marker_color=PALETTE[0]))
    else:
        return None
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)" if dark else "#FFFFFF", plot_bgcolor="rgba(0,0,0,0)" if dark else "#FFFFFF",
        font=dict(color=fg), margin=dict(l=50, r=20, t=30, b=50), showlegend=False,
        xaxis_title=str(x), yaxis_title=str(y) if kind != "hist" else "Count",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#334155" if dark else "#E2E8F0")
    return fig

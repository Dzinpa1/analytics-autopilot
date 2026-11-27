"""analyses.py - deterministic analysis library used to answer objectives.

Every function takes a prepared dataframe (original column names, NaN for blanks) plus a spec and
returns a Finding. Nothing here calls an LLM and nothing invents numbers: wording is generated from
computed values only, and every Finding carries its coverage and caveats.
"""
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import pandas as pd

from data_quality import summarize_center

MONEY_WORDS = {"revenue", "sales", "cost", "costs", "spend", "price", "profit", "budget", "amount", "income",
               "expense", "expenses", "salary", "wage", "wages", "fee", "fees", "payment", "balance", "value", "total"}
LOWER_IS_BETTER_WORDS = {"cost", "costs", "expense", "expenses", "wait", "waiting", "delay", "delays", "defect", "defects",
                         "error", "errors", "complaint", "complaints", "churn", "loss", "losses", "downtime", "return",
                         "returns", "refund", "refunds", "cancel", "cancellation", "mortality", "failure", "failures",
                         "absence", "turnover", "duration", "latency"}
RATE_WORDS = {"rate", "ratio", "percent", "pct", "score", "avg", "average", "mean", "price", "temperature", "age",
              "margin", "index", "grade", "rating", "level", "utilization", "yield", "efficiency", "speed",
              # durations and physical measurements are averaged, never added up
              "wait", "waiting", "time", "duration", "delay", "latency", "min", "mins", "minutes", "hours", "hrs", "length",
              "size", "weight", "height", "distance", "temperature", "satisfaction", "occupancy", "uptime"}


@dataclass
class Finding:
    objective_id: str
    kind: str
    question: str
    status: str = "ok"                      # ok | caution | blocked | error
    headline: str = ""
    details: list = field(default_factory=list)
    table: Optional[pd.DataFrame] = None
    chart: Optional[dict] = None            # {"type": "line|bar|scatter|waterfall", "x": col, "y": col, ...}
    caveats: list = field(default_factory=list)
    assumptions: list = field(default_factory=list)
    coverage_pct: float = 100.0
    n_rows: int = 0
    confidence: str = "high"                # high | medium | low
    numbers: dict = field(default_factory=dict)   # machine-readable facts used in the headline


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------
def col_words(name: str) -> set:
    import re
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(name))
    return {t for t in re.split(r"[^a-z0-9]+", spaced.lower()) if t}


def is_money(col: str) -> bool:
    return bool(col_words(col) & MONEY_WORDS)


def lower_is_better(col: str) -> bool:
    return bool(col_words(col) & LOWER_IS_BETTER_WORDS)


def default_agg(col: str) -> str:
    """Quantities add up (sum); rates/scores/prices do not (mean)."""
    w = col_words(col)
    if w & RATE_WORDS and not (w & {"total", "sum"}):
        return "mean"
    return "sum"


def fmt(v, money: bool = False, sym: str = "") -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "n/a"
    a = abs(v)
    pre = sym if money else ""
    sign = "-" if v < 0 else ""
    if a >= 1e9:
        s = f"{a / 1e9:.2f}B"
    elif a >= 1e6:
        s = f"{a / 1e6:.2f}M"
    elif a >= 1e4:
        s = f"{a:,.0f}"
    elif a >= 100:
        s = f"{a:,.0f}"
    elif a >= 1:
        s = f"{a:,.2f}"
    else:
        s = f"{a:.3g}"
    return f"{sign}{pre}{s}"


def pct(v) -> str:
    return "n/a" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:+.1f}%"


def _agg_series(s: pd.Series, agg: str) -> float:
    s = s.dropna()
    if s.empty:
        return np.nan
    return float({"sum": s.sum, "mean": s.mean, "median": s.median, "count": s.count}[agg]())


def _grain_for(span_days: int) -> str:
    if span_days <= 14:
        return "D"
    if span_days <= 120:
        return "W"
    if span_days <= 365 * 5:
        return "M"
    return "Q"


_GRAIN_NAME = {"D": "day", "W": "week", "M": "month", "Q": "quarter"}


def period_table(df: pd.DataFrame, date_col: str, measure: str, agg: str, grain: Optional[str] = None) -> tuple:
    """Aggregate a measure per calendar period. Empty periods are NaN (not 0). Marks partial edge periods.
    Returns (table[period,label,value,n,partial], grain)."""
    d = df[[date_col, measure]].dropna(subset=[date_col]).copy()
    if d.empty:
        return pd.DataFrame(columns=["period", "label", "value", "n", "partial"]), grain or "M"
    span = int((d[date_col].max() - d[date_col].min()).days) + 1
    grain = grain or _grain_for(span)
    freq = {"D": "D", "W": "W-MON", "M": "M", "Q": "Q"}[grain]
    d["period"] = d[date_col].dt.to_period(freq)
    g = d.groupby("period")[measure].agg(value=lambda s: _agg_series(s, agg), n="count")
    full = pd.period_range(g.index.min(), g.index.max(), freq=freq)
    g = g.reindex(full)
    g["n"] = g["n"].fillna(0).astype(int)
    g.loc[g["n"] == 0, "value"] = np.nan
    g.index.name = "period"
    g = g.reset_index()
    fmt_map = {"D": "%d %b %Y", "W": "wk %d %b %Y", "M": "%b %Y", "Q": "Q%q %Y"}
    if grain == "Q":
        g["label"] = g["period"].map(lambda p: f"Q{p.quarter} {p.year}")
    elif grain == "W":
        g["label"] = g["period"].map(lambda p: "wk " + p.start_time.strftime("%d %b %Y"))
    else:
        g["label"] = g["period"].dt.strftime(fmt_map[grain])
    g["partial"] = False
    if len(g) >= 3 and grain in ("W", "M", "Q"):
        dates_per_period = d.groupby("period")[date_col].apply(lambda x: x.dt.normalize().nunique())
        if float(dates_per_period.median()) >= 3:      # dense enough for edge detection
            tol = pd.Timedelta(days={"W": 1, "M": 3, "Q": 7}[grain])
            if d[date_col].min() > g["period"].iloc[0].start_time + tol:
                g.loc[g.index[0], "partial"] = True
            if d[date_col].max() < g["period"].iloc[-1].end_time.normalize() - tol:
                g.loc[g.index[-1], "partial"] = True
    return g, grain


def _confidence(coverage: float, n: int, base: str = "high") -> str:
    order = ["low", "medium", "high"]
    i = order.index(base)
    if coverage < 80 or n < 20:
        i = min(i, 1)
    if coverage < 50 or n < 8:
        i = 0
    return order[i]


def _cov(df: pd.DataFrame, cols: list) -> float:
    cols = [c for c in cols if c]
    if not cols or df.empty:
        return 100.0
    return round(float(df[cols].notna().all(axis=1).mean() * 100), 1)


# ---------------------------------------------------------------------------------------------
# 1. TREND
# ---------------------------------------------------------------------------------------------
def analyze_trend(df, schema, spec, sym="") -> Finding:
    m, dc, agg = spec.measure, schema.date, spec.agg
    money = is_money(m) and spec.agg != "count"
    f = Finding(spec.id, "trend", spec.text, assumptions=list(spec.assumptions))
    sub = df[[dc, m]].dropna(subset=[dc])
    f.n_rows = int(sub[m].notna().sum())
    f.coverage_pct = _cov(df, [dc, m])
    tbl, grain = period_table(sub, dc, m, agg)
    gname = _GRAIN_NAME[grain]
    use = tbl[~tbl["partial"] & tbl["value"].notna()].copy()
    f.table = tbl[["label", "value", "n", "partial"]].rename(columns={"label": "Period", "value": m, "n": "Records", "partial": "Partial period"})
    f.chart = {"type": "line", "x": "Period", "y": m}
    if tbl["partial"].any():
        f.caveats.append("Incomplete first/last " + gname + " left out of the trend maths: " + ", ".join(tbl.loc[tbl["partial"], "label"]))
    if tbl["value"].isna().any():
        f.caveats.append(f"{int(tbl['value'].isna().sum())} {gname}(s) have no data and are shown as gaps, not zero")
    if len(use) < 3:
        f.status, f.confidence = "caution", "low"
        f.headline = f"Only {len(use)} complete {gname}(s) of data, which is not enough to call a trend."
        return f
    y = use["value"].to_numpy(dtype=float)
    x = np.arange(len(y), dtype=float)
    first, last = y[0], y[-1]
    change = (last - first) / abs(first) * 100 if (first > 0 and last >= 0) else np.nan
    slope, intercept = np.polyfit(x, y, 1)
    fitted = slope * x + intercept
    ss_res, ss_tot = float(((y - fitted) ** 2).sum()), float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    rel_slope = slope / abs(y.mean()) * 100 if y.mean() != 0 else 0.0     # % of average per period
    best, worst = use.loc[use["value"].idxmax()], use.loc[use["value"].idxmin()]
    direction = "rose" if last > first else "fell"
    clear = r2 >= 0.5 and abs(rel_slope) >= 1.0 and not np.isnan(change) and abs(change) >= 10
    lab_a, lab_b = use["label"].iloc[0], use["label"].iloc[-1]
    if clear:
        f.headline = (f"{m} {direction} from {fmt(first, money, sym)} in {lab_a} to {fmt(last, money, sym)} in {lab_b} "
                      f"({pct(change)}), a steady {'increase' if slope > 0 else 'decline'} of about {abs(rel_slope):.1f}% of the average per {gname}.")
    else:
        f.headline = (f"{m} shows no clear trend: it moved between {fmt(use['value'].min(), money, sym)} and {fmt(use['value'].max(), money, sym)} "
                      f"per {gname}" + (f", ending {pct(change)} versus the start." if not np.isnan(change) else "."))
        f.confidence = "medium"
    f.details = [f"Highest {gname}: {best['label']} ({fmt(best['value'], money, sym)}). Lowest: {worst['label']} ({fmt(worst['value'], money, sym)}).",
                 f"Straight-line fit explains {r2 * 100:.0f}% of the variation across {len(use)} {gname}s."]
    if len(use) >= 6:
        mad = float(np.median(np.abs(y - np.median(y))))
        if mad > 0:
            z = 0.6745 * (y - np.median(y)) / mad
            odd = use.loc[np.abs(z) > 3.5, "label"].tolist()
            if odd:
                f.details.append("Unusual " + gname + "(s) compared with the rest: " + ", ".join(odd))
    f.numbers = {"first": first, "last": last, "change_pct": None if np.isnan(change) else float(change), "r2": r2, "grain": gname}
    f.confidence = _confidence(f.coverage_pct, f.n_rows, f.confidence)
    if f.coverage_pct < 100:
        f.caveats.append(f"Based on the {f.coverage_pct:.0f}% of rows that have both a date and a {m} value")
    return f


# ---------------------------------------------------------------------------------------------
# 2. COMPARE (which group is highest/lowest)
# ---------------------------------------------------------------------------------------------
def analyze_compare(df, schema, spec, sym="") -> Finding:
    m, dim, agg = spec.measure, spec.dimension, spec.agg
    money = is_money(m) and agg != "count"
    f = Finding(spec.id, "compare", spec.text, assumptions=list(spec.assumptions))
    sub = df[[dim, m]].dropna(subset=[dim, m])
    f.n_rows = len(sub)
    f.coverage_pct = _cov(df, [dim, m])
    g = sub.groupby(dim)[m].agg(value=lambda s: _agg_series(s, agg), n="count").reset_index()
    if len(g) < 2:
        f.status, f.confidence = "blocked", "low"
        f.headline = f"'{dim}' has only one group in the data, so there is nothing to compare."
        return f
    asc = spec.direction == "low"
    g = g.sort_values("value", ascending=asc).reset_index(drop=True)
    total = float(g["value"].sum()) if agg in ("sum", "count") else np.nan
    if agg in ("sum", "count") and total > 0 and (g["value"] >= 0).all():
        g["share_pct"] = (g["value"] / total * 100).round(1)
    top, bottom = g.iloc[0], g.iloc[-1]
    label = {"sum": "total", "mean": "average", "median": "median", "count": "number of records for"}[agg]
    word = "lowest" if asc else "highest"
    f.table = g.rename(columns={"value": f"{label.title()} {m}".strip(), "n": "Records", "share_pct": "Share %"}).head(max(spec.top_n, 5) if len(g) > 12 else len(g))
    f.chart = {"type": "bar", "x": dim, "y": f"{label.title()} {m}".strip()}
    f.headline = f"{top[dim]} has the {word} {label} {m}: {fmt(top['value'], money, sym)}"
    if "share_pct" in g.columns:
        f.headline += f" ({top['share_pct']:.0f}% of the total)"
    f.headline += f", versus {fmt(bottom['value'], money, sym)} for {bottom[dim]}."
    hi_v, lo_v = float(g["value"].max()), float(g["value"].min())
    if lo_v > 0 and hi_v / lo_v >= 1.5:
        f.details.append(f"The highest group is {hi_v / lo_v:.1f} times the lowest.")
    small = g[g["n"] < 5]
    if agg in ("mean", "median") and len(small):
        f.caveats.append(f"{len(small)} group(s) have fewer than 5 records, so their {label} is unreliable: " + ", ".join(map(str, small[dim].head(5))))
    if agg in ("mean", "median") and len(g) >= 2:
        a = sub[sub[dim] == top[dim]][m]
        b = sub[sub[dim] != top[dim]][m]
        if len(a) >= 5 and len(b) >= 5 and (a.std() + b.std()) > 0:
            pooled = np.sqrt(((len(a) - 1) * a.var() + (len(b) - 1) * b.var()) / (len(a) + len(b) - 2))
            d = (a.mean() - b.mean()) / pooled if pooled > 0 else 0.0
            f.numbers["effect_size_d"] = float(d)
            if abs(d) < 0.3:
                f.caveats.append(f"The gap between {top[dim]} and the rest is small compared with the normal spread in {m} (effect size {abs(d):.2f}), so the ranking may not be meaningful.")
                f.confidence = "medium"
    if agg == "mean":
        c = summarize_center(sub[m])
        if c["is_skewed"]:
            f.caveats.append(f"{m} is skewed (a few very large values), so averages can mislead; the overall median is {fmt(c['median'], money, sym)} against a mean of {fmt(c['mean'], money, sym)}.")
    if len(g) > 12:
        f.caveats.append(f"{len(g)} groups in total; showing the top {len(f.table)}")
    f.numbers.update({"top": str(top[dim]), "top_value": float(top["value"]), "bottom": str(bottom[dim]), "bottom_value": float(bottom["value"])})
    f.confidence = _confidence(f.coverage_pct, f.n_rows, f.confidence)
    if f.coverage_pct < 100:
        f.caveats.append(f"Based on the {f.coverage_pct:.0f}% of rows that have both {dim} and {m}")
    return f


# ---------------------------------------------------------------------------------------------
# 3. CHANGE ("why did X drop in Q3?") - where did the change come from
# ---------------------------------------------------------------------------------------------
def _slice(df, dc, rng):
    s, e = rng
    return df[(df[dc] >= s) & (df[dc] <= e)]


def analyze_change(df, schema, spec, sym="") -> Finding:
    m, dc, agg = spec.measure, schema.date, spec.agg
    money = is_money(m) and spec.agg != "count"
    f = Finding(spec.id, "change", spec.text, assumptions=list(spec.assumptions))
    base_rng, focus_rng = spec.base_range, spec.focus_range
    base, focus = _slice(df, dc, base_rng), _slice(df, dc, focus_rng)
    f.n_rows = int(base[m].notna().sum() + focus[m].notna().sum())
    f.coverage_pct = _cov(pd.concat([base, focus]), [dc, m])
    if base[m].notna().sum() == 0 or focus[m].notna().sum() == 0:
        f.status, f.confidence = "blocked", "low"
        have = df[dc].dropna()
        rng = f" Your data covers {have.min():%d %b %Y} to {have.max():%d %b %Y}." if len(have) else ""
        f.headline = f"There is no {m} data in one of the two periods ({spec.base_label} / {spec.focus_label}), so they cannot be compared.{rng}"
        return f
    vb, vf = _agg_series(base[m], agg), _agg_series(focus[m], agg)
    delta = vf - vb
    pc = delta / abs(vb) * 100 if (vb and vb > 0 and vf >= 0) else np.nan   # % is meaningless across zero/negative bases
    verb = "rose" if delta > 0 else "fell" if delta < 0 else "did not change"
    label = {"sum": "total", "mean": "average", "median": "median", "count": "record count of"}[agg]
    f.headline = (f"{label.capitalize()} {m} {verb} from {fmt(vb, money, sym)} in {spec.base_label} to {fmt(vf, money, sym)} in {spec.focus_label}"
                  f" ({pct(pc) + ', ' if not np.isnan(pc) else ''}{fmt(delta, money, sym)}).")
    f.numbers = {"base": vb, "focus": vf, "delta": delta, "pct": None if np.isnan(pc) else float(pc)}
    low = spec.text.lower()
    asked_down = any(w in low for w in ("drop", "fall", "fell", "decline", "decrease", "dip", "went down", "lower", "worse"))
    asked_up = any(w in low for w in ("rise", "rose", "increase", "jump", "spike", "surge", "grew", "higher", "went up"))
    if asked_down and not asked_up and delta > 0:
        f.details.insert(0, f"Note: your question assumes a drop, but {m} actually went UP between these periods.")
    elif asked_up and not asked_down and delta < 0:
        f.details.insert(0, f"Note: your question assumes an increase, but {m} actually went DOWN between these periods.")
    # comparable length?
    len_b = (base_rng[1] - base_rng[0]).days + 1
    len_f = (focus_rng[1] - focus_rng[0]).days + 1
    if agg == "sum" and abs(len_b - len_f) / max(len_b, len_f) > 0.10:
        pdb, pdf = vb / len_b, vf / len_f
        f.caveats.append(f"The periods differ in length ({len_b} vs {len_f} days). Per day, {m} went from {fmt(pdb, money, sym)} to {fmt(pdf, money, sym)} ({pct((pdf - pdb) / abs(pdb) * 100 if pdb else np.nan)}).")
    # partial periods (data doesn't reach the end of the period)
    for lab, rng, part in ((spec.base_label, base_rng, base), (spec.focus_label, focus_rng, focus)):
        if len(part) and (part[dc].max() < rng[1] - pd.Timedelta(days=3) or part[dc].min() > rng[0] + pd.Timedelta(days=3)):
            f.caveats.append(f"Data for {lab} does not cover the whole period ({part[dc].min():%d %b} to {part[dc].max():%d %b}), which can distort the comparison.")
    # decomposition
    rows = []
    for dim in schema.dimensions:
        levels = df[dim].nunique(dropna=True)
        if levels < 2 or levels > 40 or dim == dc:
            continue
        b = base.groupby(dim)[m].agg(lambda s: _agg_series(s, agg))
        fo = focus.groupby(dim)[m].agg(lambda s: _agg_series(s, agg))
        t = pd.concat([b.rename("base"), fo.rename("focus")], axis=1).fillna(0.0)
        t["change"] = t["focus"] - t["base"]
        if agg == "sum" and delta != 0:
            t["share_of_change_pct"] = t["change"] / delta * 100
            lead = t["change"].abs().idxmax()
            rows.append((dim, lead, float(t.loc[lead, "change"]), float(t.loc[lead, "share_of_change_pct"]), t))
        else:
            lead = t["change"].abs().idxmax()
            rows.append((dim, lead, float(t.loc[lead, "change"]), np.nan, t))
    if rows:
        if agg == "sum" and delta != 0:
            rows.sort(key=lambda r: -abs(r[3]))
        else:
            rows.sort(key=lambda r: -abs(r[2]))
        dim, lead, ch, share, t = rows[0]
        if agg == "sum" and delta != 0:
            f.details.append(f"Biggest single driver: {dim} = {lead}, {fmt(ch, money, sym)} change, which is {abs(share):.0f}% of the net change"
                             + (" (more than all of it, other groups moved the opposite way)." if abs(share) > 100 else "."))
        else:
            f.details.append(f"Largest move: {dim} = {lead} ({fmt(ch, money, sym)}).")
        for dim2, lead2, ch2, share2, _ in rows[1:3]:
            f.details.append(f"Also: {dim2} = {lead2} ({fmt(ch2, money, sym)}" + (f", {abs(share2):.0f}% of net change" if not np.isnan(share2) else "") + ").")
        out = t.reset_index().rename(columns={dim: dim, "base": spec.base_label, "focus": spec.focus_label, "change": "Change", "share_of_change_pct": "Share of net change %"})
        out = out.reindex(out["Change"].abs().sort_values(ascending=False).index).head(10)
        f.table = out.round(2)
        f.chart = {"type": "bar", "x": dim, "y": "Change"}
        f.numbers["driver_dimension"], f.numbers["driver_level"] = dim, str(lead)
    else:
        f.caveats.append("No grouping column with 2-40 levels was found, so the change cannot be broken down by group.")
    f.caveats.append("This shows WHERE and WHEN the change happened. The data alone cannot prove WHY it happened.")
    f.confidence = _confidence(f.coverage_pct, f.n_rows, "high" if rows else "medium")
    if f.coverage_pct < 100:
        f.caveats.append(f"Based on the {f.coverage_pct:.0f}% of rows that have both a date and a {m} value")
    return f


# ---------------------------------------------------------------------------------------------
# 4. TARGET (actual vs budget / target)
# ---------------------------------------------------------------------------------------------
def analyze_target(df, schema, spec, sym="") -> Finding:
    a, t, dim = spec.measure, spec.measure2, spec.dimension
    money = is_money(a) or is_money(t)
    f = Finding(spec.id, "target", spec.text, assumptions=list(spec.assumptions))
    both = df.dropna(subset=[a, t])
    f.n_rows = len(both)
    f.coverage_pct = _cov(df, [a, t])
    if both.empty:
        f.status, f.confidence = "blocked", "low"
        f.headline = f"No row has both '{a}' and '{t}', so they cannot be compared."
        return f
    tot_a, tot_t = float(both[a].sum()), float(both[t].sum())
    var = tot_a - tot_t
    util = tot_a / tot_t * 100 if tot_t else np.nan
    state = "over" if var > 0 else "under" if var < 0 else "exactly on"
    f.headline = (f"{a} totals {fmt(tot_a, money, sym)} against {fmt(tot_t, money, sym)} for {t}: "
                  f"{fmt(abs(var), money, sym)} {state}" + (f" ({util:.1f}% of {t})." if not np.isnan(util) else "."))
    f.numbers = {"actual": tot_a, "target": tot_t, "variance": var, "ratio_pct": None if np.isnan(util) else float(util)}
    if dim:
        g = both.groupby(dim).agg(actual=(a, "sum"), target=(t, "sum"))
        g["variance"] = g["actual"] - g["target"]
        g["actual_vs_target_pct"] = (g["actual"] / g["target"].replace(0, np.nan) * 100).round(1)
        g = g.sort_values("variance", ascending=False).reset_index()
        f.table = g.rename(columns={"actual": a, "target": t, "variance": "Variance", "actual_vs_target_pct": f"{a} as % of {t}"})
        f.chart = {"type": "bar", "x": dim, "y": "Variance"}
        worst = g.iloc[0]
        f.details.append(f"Largest overshoot: {worst[dim]} ({fmt(worst['variance'], money, sym)}); largest undershoot: {g.iloc[-1][dim]} ({fmt(g.iloc[-1]['variance'], money, sym)}).")
    f.caveats.append(f"Compared only on the {len(both):,} rows where both {a} and {t} exist, so totals are like-for-like.")
    f.confidence = _confidence(f.coverage_pct, f.n_rows)
    return f


# ---------------------------------------------------------------------------------------------
# 5. RELATIONSHIP
# ---------------------------------------------------------------------------------------------
def analyze_relationship(df, schema, spec, sym="") -> Finding:
    x, y = spec.measure2, spec.measure
    f = Finding(spec.id, "relationship", spec.text, assumptions=list(spec.assumptions))
    pair = df[[x, y]].dropna()
    f.n_rows = len(pair)
    f.coverage_pct = _cov(df, [x, y])
    if len(pair) < 10 or pair[x].nunique() < 3 or pair[y].nunique() < 3:
        f.status, f.confidence = "blocked", "low"
        f.headline = f"Not enough paired data (need at least 10 rows with varied values) to measure a relationship between {x} and {y}."
        return f
    r = float(pair[x].corr(pair[y]))
    rho = float(pair[x].corr(pair[y], method="spearman"))
    slope, intercept = np.polyfit(pair[x].to_numpy(float), pair[y].to_numpy(float), 1)
    a = abs(r)
    strength = "negligible" if a < 0.2 else "weak" if a < 0.4 else "moderate" if a < 0.6 else "strong" if a < 0.8 else "very strong"
    way = "positive" if r > 0 else "negative"
    f.headline = f"{x} and {y} have a {strength}{'' if strength == 'negligible' else ' ' + way} relationship (correlation {r:+.2f}, {len(pair):,} rows)."
    if strength != "negligible":
        f.details.append(f"On average, each 1-unit increase in {x} goes with a {slope:+.3g} change in {y}.")
    if abs(r - rho) > 0.2:
        f.caveats.append(f"Pearson ({r:+.2f}) and rank-based ({rho:+.2f}) correlations disagree, which usually means a few extreme values are driving the result.")
        f.confidence = "medium"
    f.caveats.append("Correlation shows that two things move together, not that one causes the other.")
    sample = pair.sample(min(len(pair), 500), random_state=0) if len(pair) > 500 else pair
    f.table = sample.rename_axis(None).reset_index(drop=True)
    f.chart = {"type": "scatter", "x": x, "y": y}
    f.numbers = {"pearson": r, "spearman": rho, "slope": float(slope), "n": len(pair)}
    f.confidence = _confidence(f.coverage_pct, f.n_rows, f.confidence)
    return f


# ---------------------------------------------------------------------------------------------
# 6. COMPOSITION (shares)
# ---------------------------------------------------------------------------------------------
def analyze_composition(df, schema, spec, sym="") -> Finding:
    m, dim = spec.measure, spec.dimension
    money = is_money(m)
    f = Finding(spec.id, "composition", spec.text, assumptions=list(spec.assumptions))
    sub = df[[dim, m]].dropna()
    f.n_rows = len(sub)
    f.coverage_pct = _cov(df, [dim, m])
    if (sub[m] < 0).any():
        f.caveats.append(f"{m} has negative values, so shares can add up to more than 100% for some groups.")
    g = sub.groupby(dim)[m].sum().sort_values(ascending=False)
    total = float(g.sum())
    if len(g) < 2 or total <= 0:
        f.status, f.confidence = "blocked", "low"
        f.headline = "There is nothing to break down (one group, or the total is zero or negative so shares would be meaningless)."
        return f
    share = (g / total * 100)
    top3 = float(share.head(3).sum())
    f.headline = f"{share.index[0]} is the largest part of {m} at {share.iloc[0]:.0f}% ({fmt(g.iloc[0], money, sym)}); the top {min(3, len(g))} groups make up {top3:.0f}%."
    shown = pd.DataFrame({dim: g.index, m: g.values, "Share %": share.round(1).values})
    if len(shown) > 10:
        other = shown.iloc[9:]
        shown = pd.concat([shown.iloc[:9], pd.DataFrame([{dim: f"Other ({len(other)} groups)", m: other[m].sum(), "Share %": round(float(other["Share %"].sum()), 1)}])], ignore_index=True)
    f.table = shown
    f.chart = {"type": "bar", "x": dim, "y": "Share %"}
    if top3 >= 80 and len(g) > 4:
        f.details.append(f"Highly concentrated: {top3:.0f}% sits in just 3 of {len(g)} groups.")
    f.numbers = {"top": str(share.index[0]), "top_share_pct": float(share.iloc[0]), "top3_share_pct": top3}
    f.confidence = _confidence(f.coverage_pct, f.n_rows)
    if f.coverage_pct < 100:
        f.caveats.append(f"Shares are of the {f.coverage_pct:.0f}% of rows that have both {dim} and {m}")
    return f


# ---------------------------------------------------------------------------------------------
# 7. DISTRIBUTION / OUTLIERS
# ---------------------------------------------------------------------------------------------
def analyze_distribution(df, schema, spec, sym="") -> Finding:
    m = spec.measure
    money = is_money(m)
    f = Finding(spec.id, "distribution", spec.text, assumptions=list(spec.assumptions))
    s = df[m].dropna()
    f.n_rows = len(s)
    f.coverage_pct = _cov(df, [m])
    if len(s) < 8:
        f.status, f.confidence = "blocked", "low"
        f.headline = f"Only {len(s)} {m} value(s): too few to describe a distribution."
        return f
    c = summarize_center(s)
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    mask = (df[m] < lo) | (df[m] > hi)
    n_out = int(mask.sum())
    f.headline = (f"Typical {m} is {fmt(c['median'], money, sym)} (median); the average is {fmt(c['mean'], money, sym)}. "
                  + (f"{n_out} value(s) ({n_out / len(s) * 100:.1f}%) are unusually far from the rest." if n_out else "No unusual values were found."))
    if c["is_skewed"]:
        f.details.append(f"The data is skewed, so the median ({fmt(c['median'], money, sym)}) describes a typical case better than the mean ({fmt(c['mean'], money, sym)}).")
    f.details.append(f"Middle 50% of values: {fmt(q1, money, sym)} to {fmt(q3, money, sym)}. Range: {fmt(s.min(), money, sym)} to {fmt(s.max(), money, sym)}.")
    if n_out:
        extreme = df.loc[mask].assign(_d=(df.loc[mask, m] - s.median()).abs()).sort_values("_d", ascending=False).drop(columns="_d").head(10)
        f.table = extreme
        f.caveats.append("Unusual values are not necessarily errors: check them against the source before removing anything.")
    f.chart = {"type": "hist", "x": m}
    f.numbers = {"median": c["median"], "mean": c["mean"], "skew": c["skew"], "outliers": n_out}
    f.confidence = _confidence(f.coverage_pct, f.n_rows)
    return f


# ---------------------------------------------------------------------------------------------
# 8. OVERVIEW (no specific question)
# ---------------------------------------------------------------------------------------------
def analyze_overview(df, schema, spec, sym="") -> Finding:
    m, agg = spec.measure, spec.agg
    money = is_money(m)
    f = Finding(spec.id, "overview", spec.text, assumptions=list(spec.assumptions))
    s = df[m].dropna()
    f.n_rows = len(s)
    f.coverage_pct = _cov(df, [m])
    if s.empty:
        f.status, f.confidence = "blocked", "low"
        f.headline = f"'{m}' has no values."
        return f
    c = summarize_center(s)
    total = fmt(float(s.sum()), money, sym)
    f.headline = f"{m}: {len(s):,} records, total {total}, median {fmt(c['median'], money, sym)}, average {fmt(c['mean'], money, sym)}."
    if c["is_skewed"]:
        f.details.append("Skewed distribution: prefer the median for a typical value.")
    parts = []
    if schema.date:
        try:
            sub_spec = type(spec)(**{**spec.__dict__, "id": spec.id + "-t", "kind": "trend"})
            tr = analyze_trend(df, schema, sub_spec, sym)
            parts.append(tr)
            f.details.append("Trend: " + tr.headline)
        except Exception:
            pass
    if schema.dimensions:
        dim = spec.dimension or schema.dimensions[0]
        sub_spec = type(spec)(**{**spec.__dict__, "id": spec.id + "-c", "kind": "compare", "dimension": dim, "direction": "high"})
        cm = analyze_compare(df, schema, sub_spec, sym)
        if cm.status != "blocked":
            parts.append(cm)
            f.details.append("By " + dim + ": " + cm.headline)
            f.table, f.chart = cm.table, cm.chart
    f.caveats = sorted({c_ for p in parts for c_ in p.caveats})
    f.numbers = {"total": float(s.sum()), "median": c["median"], "mean": c["mean"]}
    f.confidence = _confidence(f.coverage_pct, f.n_rows)
    return f


ANALYSES = {
    "trend": analyze_trend, "compare": analyze_compare, "change": analyze_change, "target": analyze_target,
    "relationship": analyze_relationship, "composition": analyze_composition,
    "distribution": analyze_distribution, "overview": analyze_overview,
}

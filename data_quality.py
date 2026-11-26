"""data_quality.py - missing-data profiling, decision gate, handling policies and relational fills.

Pure pandas/numpy (no Streamlit) so every function is unit-testable.

Design rules
------------
* Missing is NOT zero. Nothing here turns a blank into 0 unless the caller explicitly chooses
  the "fill_zero" policy.
* Every change is recorded: a human-readable log plus boolean masks that say which cells were
  filled/derived, so downstream KPIs can report how much of a number is estimated.
* Relational fills (e.g. profit = revenue - cost) only use values that were actually measured
  in the same row, and never chain from other filled values.
"""
from dataclasses import dataclass, field
from typing import Callable, Optional
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Gate thresholds (percent of a column's rows that are missing)
# ---------------------------------------------------------------------------
GATE_OK_BELOW = 5.0         # < 5%   : proceed
GATE_CAUTION_BELOW = 20.0   # 5-20%  : proceed with a visible warning
GATE_DECISION_BELOW = 40.0  # 20-40% : the user must choose how to handle it
                            # >= 40% : recommend not reporting on it (user can override)

LEVEL_ORDER = {"ok": 0, "caution": 1, "decision": 2, "blocked": 3}

POLICY_METHODS = ("keep", "drop_rows", "fill_median", "fill_mean", "fill_zero",
                  "fill_value", "ffill", "interpolate")


def gate_level(missing_pct: float) -> str:
    if missing_pct < GATE_OK_BELOW:
        return "ok"
    if missing_pct < GATE_CAUTION_BELOW:
        return "caution"
    if missing_pct < GATE_DECISION_BELOW:
        return "decision"
    return "blocked"


# ---------------------------------------------------------------------------
# Missing-data profile
# ---------------------------------------------------------------------------
def _candidate_group_columns(df: pd.DataFrame, exclude: str, max_levels: int = 30) -> list:
    out = []
    for c in df.columns:
        if c == exclude:
            continue
        s = df[c]
        if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_datetime64_any_dtype(s):
            continue
        n_unique = s.nunique(dropna=True)
        if 2 <= n_unique <= max_levels:
            out.append(c)
    return out


def _time_buckets(df: pd.DataFrame, date_col: Optional[str], bins: int = 4) -> Optional[pd.Series]:
    if not date_col or date_col not in df.columns:
        return None
    d = pd.to_datetime(df[date_col], errors="coerce")
    if d.notna().sum() < bins * 10:
        return None
    try:
        b = pd.qcut(d.rank(method="first"), q=bins, labels=False)
    except ValueError:
        return None
    first = d.groupby(b).min()
    last = d.groupby(b).max()
    labels = {k: f"{first[k]:%b %Y}-{last[k]:%b %Y}" for k in first.index}
    return b.map(labels)


def detect_missing_pattern(df: pd.DataFrame, column: str, date_col: Optional[str] = None,
                           min_group: int = 20) -> tuple:
    """Is the missingness of `column` spread evenly, or concentrated in one group/time block?

    Heuristic effect-size rule (not a formal test): a group is flagged when it has >= min_group rows
    and its missing rate is at least double, and at least 15 points higher than, the rate in the
    rows outside that group.
    Returns (pattern, detail) where pattern is 'none' | 'spread' | 'concentrated'.
    """
    miss = df[column].isna()
    n_missing = int(miss.sum())
    if n_missing == 0:
        return "none", ""
    overall = n_missing / len(df)
    findings = []
    groupers = {c: df[c] for c in _candidate_group_columns(df, column)}
    tb = _time_buckets(df, date_col)
    if tb is not None:
        groupers[f"time ({date_col})"] = tb
    for gname, gser in groupers.items():
        g = pd.DataFrame({"m": miss, "g": gser}).dropna(subset=["g"])
        stats = g.groupby("g")["m"].agg(["mean", "size"])
        stats = stats[stats["size"] >= min_group]
        if stats.empty:
            continue
        worst = stats["mean"].idxmax()
        rate_in = float(stats.loc[worst, "mean"])
        size_in = int(stats.loc[worst, "size"])
        n_rows = len(g)
        rest = n_rows - size_in
        if rest <= 0:
            continue
        miss_in = rate_in * size_in
        rate_out = (float(g["m"].sum()) - miss_in) / rest
        # compare the group with the rows OUTSIDE it (a group holding half the data can never
        # be "double the overall rate", even if every gap is inside it)
        if rate_in - rate_out >= 0.15 and rate_in >= 2 * rate_out:
            findings.append((rate_in - rate_out, f"{rate_in:.0%} missing in {gname} = '{worst}' vs {rate_out:.0%} elsewhere"))
    if findings:
        findings.sort(reverse=True)
        return "concentrated", findings[0][1]
    return "spread", "missing values look spread across groups and time"


def missing_profile(df: pd.DataFrame, columns: Optional[list] = None,
                    date_col: Optional[str] = None) -> pd.DataFrame:
    """One row per column: counts, percent, gate level and missingness pattern."""
    cols = [c for c in (columns if columns is not None else df.columns) if c in df.columns]
    rows = []
    n = len(df)
    for c in cols:
        m = int(df[c].isna().sum())
        pct = (m / n * 100.0) if n else 0.0
        pattern, detail = detect_missing_pattern(df, c, date_col) if 0 < m < n else (("none", "") if m == 0 else ("all", "column is empty"))
        rows.append({
            "column": c, "missing_n": m, "missing_pct": round(pct, 1),
            "non_missing_n": n - m, "gate": gate_level(pct),
            "pattern": pattern, "pattern_detail": detail,
        })
    return pd.DataFrame(rows, columns=["column", "missing_n", "missing_pct", "non_missing_n", "gate", "pattern", "pattern_detail"])


@dataclass
class Gate:
    level: str = "ok"                      # ok | caution | decision | blocked
    reasons: list = field(default_factory=list)
    complete_case_pct: float = 100.0       # % rows with every needed column present

    @property
    def can_proceed_by_default(self) -> bool:
        return self.level in ("ok", "caution")


def assess_gate(df: pd.DataFrame, needed_columns: list, date_col: Optional[str] = None,
                profile: Optional[pd.DataFrame] = None) -> Gate:
    """Judge ONLY the columns the analysis needs. A messy column nobody uses never blocks a result."""
    needed = [c for c in needed_columns if c in df.columns]
    if profile is None:
        profile = missing_profile(df, needed, date_col)
    prof = profile[profile["column"].isin(needed)]
    level = "ok"
    reasons = []
    for _, r in prof.iterrows():
        if LEVEL_ORDER[r["gate"]] > LEVEL_ORDER[level]:
            level = r["gate"]
        if r["gate"] != "ok":
            msg = f"'{r['column']}' is missing in {r['missing_pct']}% of rows"
            if r["pattern"] == "concentrated":
                msg += f" ({r['pattern_detail']}) - the gaps are not random, so results may be biased"
            reasons.append(msg)
        elif r["pattern"] == "concentrated":
            reasons.append(f"'{r['column']}' has few gaps but they cluster: {r['pattern_detail']}")
    cc = coverage(df, needed) * 100.0 if needed else 100.0
    if needed and cc < 100.0 - GATE_CAUTION_BELOW and LEVEL_ORDER[level] < LEVEL_ORDER["decision"]:
        level = "decision"
        reasons.append(f"only {cc:.0f}% of rows have every needed column")
    return Gate(level=level, reasons=reasons, complete_case_pct=round(cc, 1))


# ---------------------------------------------------------------------------
# Coverage / matched-row helpers (what makes KPIs honest)
# ---------------------------------------------------------------------------
def coverage(df: pd.DataFrame, columns: list) -> float:
    """Fraction (0-1) of rows where ALL the given columns are present."""
    cols = [c for c in columns if c in df.columns]
    if not cols or len(df) == 0:
        return 1.0 if not cols else 0.0
    return float(df[cols].notna().all(axis=1).mean())


def matched_sum(df: pd.DataFrame, columns: list) -> dict:
    """Sum of each column over rows where ALL listed columns are present (like-for-like)."""
    cols = [c for c in columns if c in df.columns]
    mask = df[cols].notna().all(axis=1)
    return {c: float(df.loc[mask, c].sum()) for c in cols}


def matched_ratio(df: pd.DataFrame, numerator: str, denominator: str) -> tuple:
    """sum(numerator) / sum(denominator) over rows where both exist. Returns (ratio|None, coverage 0-1)."""
    if numerator not in df.columns or denominator not in df.columns or len(df) == 0:
        return None, 0.0
    mask = df[numerator].notna() & df[denominator].notna()
    cov = float(mask.mean())
    den = float(df.loc[mask, denominator].sum())
    if not mask.any() or den == 0:
        return None, cov
    return float(df.loc[mask, numerator].sum()) / den, cov


# ---------------------------------------------------------------------------
# Distribution summary: when is the average misleading?
# ---------------------------------------------------------------------------
def summarize_center(series: pd.Series) -> dict:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) == 0:
        return {"n": 0, "mean": None, "median": None, "skew": None, "is_skewed": False,
                "outlier_pct": 0.0, "recommended": "mean"}
    mean, median = float(s.mean()), float(s.median())
    skew = float(s.skew()) if len(s) >= 3 else 0.0
    if np.isnan(skew):
        skew = 0.0
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    outliers = ((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).mean() * 100 if iqr > 0 else 0.0
    skewed = abs(skew) > 1.0 or (median != 0 and abs(mean - median) / abs(median) > 0.25)
    return {"n": int(len(s)), "mean": mean, "median": median, "skew": round(skew, 2),
            "is_skewed": bool(skewed), "outlier_pct": round(float(outliers), 1),
            "recommended": "median" if skewed else "mean"}


# ---------------------------------------------------------------------------
# Handling policies (what the user chooses per column)
# ---------------------------------------------------------------------------
@dataclass
class PolicyResult:
    df: pd.DataFrame
    log: list = field(default_factory=list)
    filled_masks: dict = field(default_factory=dict)   # column -> bool Series (True = value was filled)
    rows_dropped: int = 0


def apply_policies(df: pd.DataFrame, policies: Optional[dict]) -> PolicyResult:
    """policies: {column: {"method": <POLICY_METHODS>, "value": <for fill_value>}}.
    Unknown columns/methods raise ValueError so a typo can never silently change results."""
    out = df.copy()
    res = PolicyResult(df=out)
    policies = policies or {}

    # 1) validate everything first
    for col, pol in policies.items():
        method = (pol or {}).get("method", "keep")
        if col not in out.columns:
            raise ValueError(f"Policy refers to unknown column '{col}'.")
        if method not in POLICY_METHODS:
            raise ValueError(f"Unknown handling method '{method}' for column '{col}'.")
        if method in ("fill_median", "fill_mean", "interpolate") and not pd.api.types.is_numeric_dtype(out[col]):
            raise ValueError(f"'{method}' needs a numeric column, but '{col}' is not numeric.")
        if method == "fill_value" and (pol or {}).get("value") is None:
            raise ValueError(f"'fill_value' for '{col}' needs a value.")

    # 2) fills first (so a drop on another column sees final state), drops last
    drop_cols = []
    for col, pol in policies.items():
        method = (pol or {}).get("method", "keep")
        before = out[col].isna()
        n_miss = int(before.sum())
        if method == "keep" or n_miss == 0:
            continue
        if method == "drop_rows":
            drop_cols.append(col)
            continue
        if method == "fill_median":
            fill = out[col].median()
        elif method == "fill_mean":
            fill = out[col].mean()
        elif method == "fill_zero":
            fill = 0
        elif method == "fill_value":
            fill = pol["value"]
        elif method == "ffill":
            out[col] = out[col].ffill()
            fill = None
        elif method == "interpolate":
            out[col] = out[col].interpolate(limit_direction="both")
            fill = None
        if fill is not None:
            if pd.isna(fill):
                res.log.append(f"Could not fill '{col}' with {method}: no measured values to base it on (left missing)")
                continue
            out[col] = out[col].fillna(fill)
        filled = before & out[col].notna()
        res.filled_masks[col] = filled
        label = {"fill_median": "median", "fill_mean": "mean", "fill_zero": "0", "fill_value": f"your value {pol.get('value')!r}",
                 "ffill": "previous value", "interpolate": "interpolation"}[method]
        res.log.append(f"Filled {int(filled.sum())} missing '{col}' value(s) using {label} (marked as estimated)")

    if drop_cols:
        keep_mask = out[drop_cols].notna().all(axis=1)
        res.rows_dropped = int((~keep_mask).sum())
        if res.rows_dropped:
            res.log.append(f"Removed {res.rows_dropped} row(s) with a missing value in: {', '.join(drop_cols)}")
        out = out[keep_mask]
        res.filled_masks = {c: m[keep_mask] for c, m in res.filled_masks.items()}
    res.df = out
    return res


# ---------------------------------------------------------------------------
# Relational fills + identity checks
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Relation:
    name: str
    target: str                       # role being derived
    inputs: tuple                     # roles required
    formula: Callable                 # f(*input_series) -> series
    description: str


DEFAULT_RELATIONS = (
    Relation("profit = revenue - cost", "profit", ("revenue", "cost"), lambda r, c: r - c, "Profit is revenue minus cost"),
    Relation("cost = revenue - profit", "cost", ("revenue", "profit"), lambda r, p: r - p, "Cost is revenue minus profit"),
    Relation("revenue = cost + profit", "revenue", ("cost", "profit"), lambda c, p: c + p, "Revenue is cost plus profit"),
    Relation("revenue = quantity x unit_price", "revenue", ("quantity", "unit_price"), lambda q, u: q * u, "Revenue is quantity times unit price"),
    Relation("variance = actual - budget", "variance", ("actual", "budget"), lambda a, b: a - b, "Variance is actual minus budget"),
    Relation("actual = budget + variance", "actual", ("budget", "variance"), lambda b, v: b + v, "Actual is budget plus variance"),
)


@dataclass
class DeriveResult:
    df: pd.DataFrame
    log: list = field(default_factory=list)
    derived_masks: dict = field(default_factory=dict)   # column -> bool Series
    identity_report: list = field(default_factory=list)  # one dict per checked relation


def check_identities(df: pd.DataFrame, roles: dict, relations=DEFAULT_RELATIONS, tolerance: float = 0.01) -> list:
    """Where target and inputs are ALL measured, does the formula hold? Reports violations (likely data errors)."""
    report = []
    for rel in relations:
        needed = (rel.target,) + tuple(rel.inputs)
        if not all(r in roles and roles[r] in df.columns for r in needed):
            continue
        cols = [roles[r] for r in needed]
        sub = df[cols].dropna()
        if sub.empty:
            continue
        actual = sub[roles[rel.target]]
        expected = rel.formula(*[sub[roles[i]] for i in rel.inputs])
        scale = np.maximum(np.maximum(actual.abs(), expected.abs()), 1.0)
        bad = (actual - expected).abs() > tolerance * scale
        report.append({
            "relation": rel.name, "checked_rows": int(len(sub)), "violations": int(bad.sum()),
            "violation_pct": round(float(bad.mean() * 100), 1),
            "sample_index": [int(i) if isinstance(i, (int, np.integer)) else i for i in sub.index[bad][:5]],
        })
    return report


def derive_missing(df: pd.DataFrame, roles: dict, relations=DEFAULT_RELATIONS, tolerance: float = 0.01) -> DeriveResult:
    """Fill blanks that follow exactly from other measured columns in the same row.

    roles maps semantic role -> actual column name, e.g. {"revenue": "Sales", "cost": "COGS", "profit": "Margin"}.
    A target is derived by the FIRST applicable relation only, and only from originally-measured inputs.
    """
    out = df.copy()
    res = DeriveResult(df=out)
    res.identity_report = check_identities(df, roles, relations, tolerance)
    done_targets = set()
    for rel in relations:
        if rel.target in done_targets:
            continue
        needed = (rel.target,) + tuple(rel.inputs)
        if not all(r in roles and roles[r] in df.columns for r in needed):
            continue
        tcol = roles[rel.target]
        inputs_ok = df[[roles[i] for i in rel.inputs]].notna().all(axis=1)
        mask = df[tcol].isna() & inputs_ok            # measured inputs only (not chained)
        if not mask.any():
            continue
        values = rel.formula(*[df[roles[i]] for i in rel.inputs])
        out.loc[mask, tcol] = values[mask]
        prev = res.derived_masks.get(tcol)
        res.derived_masks[tcol] = mask if prev is None else (prev | mask)
        done_targets.add(rel.target)
        res.log.append(f"Derived {int(mask.sum())} missing '{tcol}' value(s) exactly from {rel.name} (marked as derived)")
    res.df = out
    return res


# ---------------------------------------------------------------------------
# Estimates: show a KPI with and without estimated cells
# ---------------------------------------------------------------------------
def sensitivity(kpi_fn: Callable, measured_df: pd.DataFrame, completed_df: pd.DataFrame) -> dict:
    """kpi_fn(df) -> float|None. Compare the KPI on measured data only vs. with filled/derived cells."""
    a = kpi_fn(measured_df)
    b = kpi_fn(completed_df)
    delta = None
    if a not in (None, 0) and b is not None:
        delta = round((b - a) / abs(a) * 100.0, 1)
    return {"measured_only": a, "with_estimates": b, "delta_pct": delta}

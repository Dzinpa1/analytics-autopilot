"""schema.py - generic frame preparation and column-role inference for ANY tabular dataset.

Unlike the Sales-shaped engine, this keeps the user's ORIGINAL column names and only decides what
role each column plays (date / measure / dimension / id / flag / text). Missing values are kept
as NaN; nothing is invented.
"""
import re
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import pandas as pd

from analysis_engine import parse_single_numeric, consolidate_case_variants

BLANK_TOKENS = {"", "n/a", "na", "n.a.", "-", "--", "—", "null", "none", "nan", "nil", "#n/a", "?"}
DATE_NAME_HINTS = ("date", "day", "period", "month", "time", "year", "week", "quarter", "timestamp")
STRICT_ID_HINTS = ("id", "uuid", "sku", "code", "invoice", "ref")
ID_NAME_HINTS = STRICT_ID_HINTS + ("number", "no", "key")
SUMMARY_KEYWORDS = {"total", "grand total", "subtotal", "sub total", "totals"}
# A value only counts as numeric if its WHOLE shape is number-like (symbol/code prefix, digits with
# separators, optional K/M/B/T or % suffix, optional brackets) - not "free text number 5".
_NUMERIC_SHAPE = re.compile(r"^\(?\s*[-+]?\s*(?:[A-Z]{3}\s)?[^\w\s.,()+-]{0,2}\s*[-+]?\d[\d.,\s]*(?:[KkMmBbTt]|%)?\s*\)?$")
_DATE_SHAPE = re.compile(r"(\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4})|([A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{2,4})|(\d{1,2}\s+[A-Za-z]{3,9}\.?\s+\d{2,4})|(\d{1,2}[-/][A-Za-z]{3,9}[-/]\d{2,4})|(\d{4}-\d{2})")


@dataclass
class ColumnInfo:
    name: str
    role: str                       # date | measure | dimension | id | flag | text
    n_unique: int = 0
    missing_pct: float = 0.0
    note: str = ""


@dataclass
class Schema:
    columns: dict = field(default_factory=dict)      # name -> ColumnInfo
    date: Optional[str] = None
    measures: list = field(default_factory=list)
    dimensions: list = field(default_factory=list)
    ids: list = field(default_factory=list)

    def role_of(self, name: str) -> Optional[str]:
        c = self.columns.get(name)
        return c.role if c else None


@dataclass
class PreparedFrame:
    df: pd.DataFrame
    schema: Schema
    log: list = field(default_factory=list)
    quarantine: pd.DataFrame = None


def _blank_mask(s: pd.Series) -> pd.Series:
    return s.isna() | s.astype(str).str.strip().str.lower().isin(BLANK_TOKENS)


def _date_like_share(s: pd.Series) -> float:
    """Share of non-blank values that LOOK like dates (separators / month names), judged on a sample."""
    vals = s[~_blank_mask(s)].astype(str).head(200)
    if vals.empty:
        return 0.0
    return float(vals.map(lambda v: bool(_DATE_SHAPE.search(v))).mean())


def _parse_dates(s: pd.Series) -> pd.Series:
    try:
        return pd.to_datetime(s, errors="coerce", format="mixed")
    except Exception:
        return pd.to_datetime(s, errors="coerce")


def _try_numeric(s: pd.Series) -> Optional[tuple]:
    """If >= 80% of the real (non-blank) values parse as numbers return (series, n_formatted, n_unreadable)."""
    if pd.api.types.is_numeric_dtype(s):
        return pd.to_numeric(s, errors="coerce").astype(float), 0, 0
    blank = _blank_mask(s)
    real = s[~blank]
    if real.empty:
        return None
    parsed = real.map(parse_single_numeric)
    shape = real.astype(str).str.strip().str.match(_NUMERIC_SHAPE)
    ok = parsed.map(lambda t: not t[1]) & shape
    if float(ok.mean()) < 0.8:
        return None
    out = pd.Series(np.nan, index=s.index, dtype=float)
    out.loc[real.index[ok.values]] = [t[0] for t, good in zip(parsed, ok) if good]
    n_fmt = int(sum(1 for t, good in zip(parsed, ok) if good and t[2]))
    n_bad = int((~ok).sum())
    return out, n_fmt, n_bad


def _is_flag(s: pd.Series) -> bool:
    vals = set(s.dropna().astype(str).str.strip().str.lower().unique())
    return 0 < len(vals) <= 2 and vals <= {"0", "1", "0.0", "1.0", "true", "false", "yes", "no", "y", "n"}


def _name_tokens(name: str) -> list:
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(name))          # OrderID -> Order ID
    return [t for t in re.split(r"[^a-z0-9]+", spaced.lower()) if t]


def _name_has(name: str, hints) -> bool:
    """Whole-word match on the column name ('Order ID' / 'order_id' yes; 'Paid' / 'Valid' no)."""
    return any(t in hints for t in _name_tokens(name))


def prepare_frame(raw: pd.DataFrame, date_col: Optional[str] = None, drop_exact_duplicates: bool = False,
                  max_dimension_levels: int = 50) -> PreparedFrame:
    """Clean an arbitrary dataframe non-destructively and infer column roles."""
    log = []
    df = raw.copy().reset_index(drop=True)
    if df.empty:
        raise ValueError("The file contains no rows.")

    # --- column names: strip, make unique
    seen = {}
    names = []
    for c in df.columns:
        base = str(c).strip() or "Unnamed"
        k = seen.get(base, 0)
        seen[base] = k + 1
        names.append(base if k == 0 else f"{base}_{k + 1}")
    df.columns = names

    # --- fully empty rows/columns
    empty_cols = [c for c in df.columns if _blank_mask(df[c]).all()]
    if empty_cols:
        df = df.drop(columns=empty_cols)
        log.append(f"Ignored {len(empty_cols)} completely empty column(s): {', '.join(empty_cols)}")
    empty_rows = pd.Series(False, index=df.index)
    if len(df.columns):
        empty_rows = pd.concat([_blank_mask(df[c]) for c in df.columns], axis=1).all(axis=1)
    if empty_rows.any():
        log.append(f"Ignored {int(empty_rows.sum())} completely empty row(s)")
        df = df[~empty_rows]
    if df.empty or len(df.columns) == 0:
        raise ValueError("The file has no usable data.")
    quarantine_parts = []

    # --- trailing summary rows only
    tail = df.index[-5:]
    is_sum = pd.Series(False, index=df.index)
    for c in df.columns:
        if not pd.api.types.is_numeric_dtype(df[c]):
            is_sum |= df[c].astype(str).str.strip().str.lower().isin(SUMMARY_KEYWORDS) & df.index.isin(tail)
    if is_sum.any():
        q = df[is_sum].copy()
        q["quarantine_reason"] = "Summary / Total row at end of file"
        quarantine_parts.append(q)
        df = df[~is_sum]
        log.append(f"Excluded {int(is_sum.sum())} trailing summary row(s) to prevent double-counting")

    # --- duplicates (opt-in)
    n_dup = int(df.duplicated().sum())
    if drop_exact_duplicates and n_dup:
        q = df[df.duplicated()].copy()
        q["quarantine_reason"] = "Exact duplicate row (removed at your request)"
        quarantine_parts.append(q)
        df = df[~df.duplicated()]
        log.append(f"Removed {n_dup} exact duplicate row(s) at your request")
    elif n_dup:
        log.append(f"{n_dup} exact-duplicate row(s) detected and KEPT (they may be genuine repeats)")

    # --- per-column typing
    schema = Schema()
    date_candidates = []
    for c in list(df.columns):
        s = df[c]
        info = ColumnInfo(name=c, role="text")
        if pd.api.types.is_datetime64_any_dtype(s):
            info.role = "date"
            date_candidates.append(c)
        elif pd.api.types.is_numeric_dtype(s) and pd.api.types.is_bool_dtype(s):
            info.role = "flag"
        elif not pd.api.types.is_numeric_dtype(s) and _date_like_share(s) >= 0.8:
            parsed = _parse_dates(s.where(~_blank_mask(s)))
            real = ~_blank_mask(s)
            if real.any() and float(parsed[real].notna().mean()) >= 0.8:
                n_bad = int((real & parsed.isna()).sum())
                df[c] = parsed
                info.role = "date"
                if n_bad:
                    info.note = f"{n_bad} unreadable date(s) left blank"
                    log.append(f"'{c}': {n_bad} value(s) could not be read as dates and were left blank")
                date_candidates.append(c)
        elif pd.api.types.is_numeric_dtype(s) and _name_has(c, DATE_NAME_HINTS) and s.dropna().between(20000, 60000).all() and s.notna().any():
            df[c] = pd.to_datetime(s, unit="D", origin="1899-12-30", errors="coerce")   # Excel serial dates
            info.role = "date"
            date_candidates.append(c)
        if info.role == "date":
            schema.columns[c] = info
            continue

        num = _try_numeric(s)
        if num is not None:
            vals, n_fmt, n_bad = num
            df[c] = vals
            if n_fmt:
                log.append(f"'{c}': standardized {n_fmt} formatted number(s) (currency symbols, commas, brackets, K/M)")
            if n_bad:
                log.append(f"'{c}': {n_bad} unreadable value(s) left blank (not treated as 0)")
            nn = vals.dropna()
            n_unique = int(nn.nunique())
            integer_valued = bool(len(nn) and (nn % 1 == 0).all())
            if _is_flag(vals):
                info.role = "flag"
            elif integer_valued and n_unique <= 60 and _name_has(c, ("year", "month", "quarter", "week")):
                info.role = "dimension"       # calendar parts stored as numbers are labels, not quantities
            elif integer_valued and len(nn) and _name_has(c, STRICT_ID_HINTS):
                info.role = "id"
            elif integer_valued and len(nn) and n_unique / len(nn) > 0.9 and _name_has(c, ID_NAME_HINTS):
                info.role = "id"
            elif (integer_valued and len(nn) > 20 and n_unique == len(nn) and nn.is_monotonic_increasing
                  and float(nn.iloc[0]) in (0.0, 1.0) and bool((nn.diff().dropna() == 1).all())):
                info.role = "id"      # running row number
                info.note = "looks like a running row number"
            else:
                info.role = "measure"
        else:
            txt = s.where(~_blank_mask(s))
            txt = txt.astype("string").str.strip().str.replace(r"\s+", " ", regex=True).astype(object)
            txt = txt.where(txt.notna(), np.nan)
            df[c] = txt
            nn = txt.dropna()
            n_unique = int(nn.nunique())
            ratio = n_unique / len(nn) if len(nn) else 0
            if _is_flag(nn):
                info.role = "flag"
            elif n_unique <= 12 or (n_unique <= max_dimension_levels and ratio <= 0.5):
                info.role = "dimension"
                df[c], n_changed = consolidate_case_variants(df[c])
                if n_changed:
                    log.append(f"'{c}': merged {n_changed} case-only spelling variant(s)")
            elif ratio > 0.9 and _name_has(c, ID_NAME_HINTS):
                info.role = "id"
            else:
                info.role = "text"
        info.n_unique = n_unique
        schema.columns[c] = info

    # --- primary date column
    if date_col and date_col in df.columns and schema.columns[date_col].role == "date":
        schema.date = date_col
    elif date_candidates:
        hinted = [c for c in date_candidates if _name_has(c, DATE_NAME_HINTS)]
        schema.date = (hinted or date_candidates)[0]
    # other date columns become dimensions-like secondary dates: keep as 'date' role, not primary

    for c, info in schema.columns.items():
        info.missing_pct = round(float(df[c].isna().mean() * 100), 1)
    schema.measures = [c for c, i in schema.columns.items() if i.role == "measure"]
    schema.dimensions = [c for c, i in schema.columns.items() if i.role == "dimension"]
    schema.ids = [c for c, i in schema.columns.items() if i.role == "id"]

    quarantine = pd.concat(quarantine_parts, ignore_index=True) if quarantine_parts else pd.DataFrame(columns=list(df.columns) + ["quarantine_reason"])
    df = df.reset_index(drop=True)
    if schema.date is None:
        log.append("No date column found: trend and time-period questions are unavailable for this file")
    log.insert(0, f"Prepared {len(df):,} rows x {len(df.columns)} columns: {len(schema.measures)} measure(s), {len(schema.dimensions)} grouping column(s)" + (f", date column '{schema.date}'" if schema.date else ""))
    return PreparedFrame(df=df, schema=schema, log=log, quarantine=quarantine)

"""objectives.py - turn a user's question into an analysis plan, check it is feasible, and answer it.

Flow:  text --plan_objective--> ObjectiveSpec --check_feasibility--> Feasibility --run--> Finding

* The PLAN (which columns, which comparison) can come from the rule-based planner (offline,
  deterministic) or from an LLM. An LLM plan is only accepted if it validates against the real
  schema; otherwise the rule-based plan is used. The user always sees and can edit the plan.
* The NUMBERS always come from analyses.py (deterministic). An LLM never computes anything.
"""
import re
from dataclasses import dataclass, field
from typing import Callable, Optional
import json
import numpy as np
import pandas as pd

from analyses import ANALYSES, Finding, col_words, default_agg, lower_is_better, period_table
from data_quality import Gate, assess_gate, apply_policies, derive_missing, check_identities
from schema import PreparedFrame, Schema

KINDS = ("overview", "trend", "compare", "change", "target", "relationship", "composition", "distribution")
KIND_LABELS = {
    "overview": "Overview", "trend": "Trend over time", "compare": "Compare groups", "change": "What changed between two periods",
    "target": "Actual vs target/budget", "relationship": "Relationship between two measures",
    "composition": "Share / breakdown", "distribution": "Typical values and outliers",
}
AGGS = ("sum", "mean", "median", "count")
STATUS_ORDER = {"ok": 0, "caution": 1, "decision": 2, "blocked": 3}


@dataclass
class ObjectiveSpec:
    id: str
    text: str
    kind: str = "overview"
    measure: Optional[str] = None
    measure2: Optional[str] = None            # second measure (target / relationship x-axis)
    dimension: Optional[str] = None
    agg: str = "sum"
    direction: str = "high"                   # for compare: rank highest first or lowest first
    top_n: int = 5
    base_range: Optional[tuple] = None        # change: baseline period (start, end)
    focus_range: Optional[tuple] = None       # change: period being explained
    base_label: str = ""
    focus_label: str = ""
    assumptions: list = field(default_factory=list)
    planner: str = "rules"                    # rules | llm

    def needed_columns(self, schema: Schema) -> list:
        cols = [self.measure, self.measure2, self.dimension]
        if self.kind in ("trend", "change"):
            cols.append(schema.date)
        return [c for c in cols if c]


@dataclass
class Feasibility:
    status: str = "ok"                        # ok | caution | decision | blocked
    reasons: list = field(default_factory=list)
    structural: bool = False                  # True = cannot be fixed by the user's override
    gate: Optional[Gate] = None

    @property
    def can_run(self) -> bool:
        return self.status in ("ok", "caution")


# ---------------------------------------------------------------------------------------------
# text understanding (rule-based)
# ---------------------------------------------------------------------------------------------
_STOP = {"the", "a", "an", "of", "in", "on", "for", "to", "and", "or", "by", "per", "is", "are", "was", "were", "did", "do", "does",
         "how", "what", "which", "why", "who", "where", "when", "our", "my", "we", "us", "it", "its", "that", "this", "with", "from",
         "than", "than", "has", "have", "had", "be", "been", "any", "all", "each", "across", "over", "at", "as", "much", "many"}
SYNONYMS = {
    "revenue": {"sales", "income", "turnover", "takings"}, "sales": {"revenue", "income", "turnover"},
    "cost": {"expense", "expenses", "spend", "spending", "expenditure"}, "expense": {"cost", "costs", "spend", "spending"},
    "spend": {"cost", "expense", "spending"}, "profit": {"earnings", "margin"}, "wait": {"waiting", "delay", "queue"},
    "patient": {"visit", "admission", "client"}, "student": {"pupil", "learner"}, "customer": {"client", "buyer", "shopper"},
    "employee": {"staff", "worker"}, "region": {"area", "zone", "territory", "district"}, "product": {"item", "sku"},
    "quantity": {"units", "volume", "qty", "count"}, "price": {"rate"}, "budget": {"plan", "allocation", "target"},
    "actual": {"spent", "spend", "actuals"}, "target": {"goal", "quota", "budget", "plan"},
}
_BAD_GOOD_FLIP = ("worst", "best")
_KIND_RULES = [
    ("target", ("budget", "target", "quota", "forecast", "variance", "over budget", "under budget", "vs plan", "against plan", "on track", "goal")),
    ("relationship", ("relationship", "correlat", "affect", "impact", "influence", "related", "depend", "associat", "linked", "connected", "drive ")),
    ("trend", ("trend", "over time", "monthly", "weekly", "daily", "growth", "growing", "seasonal", "trajectory", "month by month", "year over year", "progress", "evolv")),
    ("change", ("why", "drop", "decline", "fell", "fall", "decrease", "dip", "went down", "rose", "increase", "jump", "spike", "surge", "what changed",
                "compared to", "compared with", "versus", " vs ", "change between", "changed")),
    ("composition", ("share", "mix", "proportion", "breakdown", "break down", "composition", "contribut", "percentage of", "split", "make up", "makes up")),
    ("distribution", ("outlier", "unusual", "anomal", "distribution", "spread", "abnormal", "skew", "typical", "variation", "extreme")),
    ("compare", ("which", "top", "best", "worst", "highest", "lowest", "most", "least", "rank", "compare", "largest", "smallest", "biggest", "fewest", "bottom", "leading", "perform")),
]
_LOW_WORDS = ("lowest", "least", "smallest", "fewest", "bottom", "minimum", "worst")
_MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def _stem(w: str) -> str:
    for suf in ("ing", "es", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def _tokens(text: str) -> list:
    return [_stem(t) for t in re.split(r"[^a-z0-9]+", text.lower()) if t and t not in _STOP]


def _expand(tokens) -> set:
    out = set(tokens)
    for t in list(tokens):
        out |= {_stem(x) for x in SYNONYMS.get(t, ())}
    return out


_AGG_MODIFIERS = {"total", "sum", "average", "avg", "mean", "median", "min", "max", "count", "number", "net", "gross"}


def _match_columns(text: str, columns: list) -> list:
    """Return [(column, score, position)] for columns mentioned in the text, best first."""
    low = text.lower()
    toks = _tokens(text)
    exp = _expand(toks)
    results = []
    for c in columns:
        words = [_stem(w) for w in col_words(c) if w not in _STOP]
        if not words:
            continue
        sub_words = [w for w in words if w not in _AGG_MODIFIERS]
        hit = sum(1 for w in words if w in exp)
        # If the column has domain words (e.g. 'sales' in 'Total Sales'), require at least one domain hit
        # so 'Total profit' never false-matches 'Total Sales' on the modifier 'total' alone.
        if sub_words and not any(w in exp for w in sub_words):
            continue
        score = hit / len(words)
        raw = re.sub(r"[^a-z0-9]+", " ", str(c).lower()).strip()
        if raw and raw in re.sub(r"[^a-z0-9]+", " ", low):
            score += 1.0
        if score >= 0.5:
            positions = [i for i, t in enumerate(toks) if t in words or t in {_stem(x) for w in words for x in SYNONYMS.get(w, ())}]
            results.append((c, score, positions[0] if positions else 999))
    results.sort(key=lambda r: (-r[1], r[2]))
    return results


def _detect_kind(text: str) -> str:
    low = " " + text.lower() + " "
    for kind, words in _KIND_RULES:
        if any(w in low for w in words):
            return kind
    return "overview"


def _clause_for_measure(text: str, measure: str) -> str:
    """Return the comma/and clause that contains `measure` so modifiers on other items don't bleed over."""
    parts = [p.strip() for p in re.split(r"\s*(?:,|;|\band\b|&)\s*", text, flags=re.I) if p.strip()]
    if len(parts) <= 1:
        return text
    m_words = {_stem(w) for w in col_words(measure) if w not in _STOP}
    best, best_hits = None, 0
    for p in parts:
        p_exp = _expand(_tokens(p))
        hits = sum(1 for w in m_words if w in p_exp)
        if hits > best_hits:
            best_hits, best = hits, p
    return best if best is not None else text


def _agg_from_clause(clause: str, measure: str) -> tuple:
    """Determine aggregation purely from a single clause."""
    low = clause.lower()
    if re.search(r"\b(median)\b", low):
        return "median", "Using the median because you asked for it.", True
    if re.search(r"\b(average|mean|avg|typical)\b", low):
        return "mean", "Using the average because you asked for it.", True
    if re.search(r"how many|number of|\bcount\b", low):
        return "count", "Counting records because the question asks 'how many'.", True
    if re.search(r"\b(total|sum)\b", low):
        return "sum", "Adding values up because you asked for the total.", True
    agg = default_agg(measure)
    why = ("adding the values up (it looks like an amount or quantity)" if agg == "sum"
           else "averaging (it looks like a rate, score or price, which should not be added up)")
    return agg, f"For '{measure}' I am {why}. Change this if that is wrong.", False


def _agg_from_text(text: str, measure: str) -> tuple:
    """Returns (agg, explanation, explicit) scoped to the clause mentioning `measure`."""
    clause = _clause_for_measure(text, measure)
    return _agg_from_clause(clause, measure)


def extract_requested_kpis(text: str, prepared: PreparedFrame) -> list:
    """Parse multi-metric questions (e.g. 'Total sales, Total profit, Number of retailers, Average days...')
    into an ordered list of clean KPI specs: {type: 'measure'|'distinct', col, agg, label}."""
    s = prepared.schema
    parts = [p.strip() for p in re.split(r"\s*(?:,|;|\band\b|&)\s*", text or "", flags=re.I) if p.strip()]
    out, seen = [], set()
    entity_cols = list(s.dimensions) + list(s.ids)

    for p in parts:
        low = p.lower()
        count_m = re.search(r"(?:number of|how many|count of|unique|distinct)\s+(.+)", low)
        if count_m and entity_cols:
            target = count_m.group(1)
            matched_ent = _match_columns(target, entity_cols)
            if not matched_ent:
                matched_ent = _match_columns(p, entity_cols)
            if matched_ent:
                col = matched_ent[0][0]
                if ("distinct", col) not in seen:
                    seen.add(("distinct", col))
                    out.append({"type": "distinct", "col": col, "agg": "nunique", "label": f"Unique {col}"})
                continue

        matched_meas = _match_columns(p, s.measures)
        if matched_meas:
            col = matched_meas[0][0]
            agg, _, _ = _agg_from_clause(p, col)
            if ("measure", col, agg) not in seen:
                seen.add(("measure", col, agg))
                out.append({"type": "measure", "col": col, "agg": agg})
    return out


# ---------------------------------------------------------------------------------------------
# periods for "what changed" questions
# ---------------------------------------------------------------------------------------------
def _month_range(y: int, m: int) -> tuple:
    s = pd.Timestamp(y, m, 1)
    return s, s + pd.offsets.MonthEnd(0) + pd.Timedelta(hours=23, minutes=59, seconds=59)


def _quarter_range(y: int, q: int) -> tuple:
    s = pd.Timestamp(y, 3 * (q - 1) + 1, 1)
    return s, s + pd.offsets.MonthEnd(3) + pd.Timedelta(hours=23, minutes=59, seconds=59)


def _shift_month(y: int, m: int, d: int) -> tuple:
    t = y * 12 + (m - 1) + d
    return t // 12, t % 12 + 1


def _latest_year_with(dates: pd.Series, test) -> Optional[int]:
    years = sorted(dates.dropna().dt.year.unique(), reverse=True)
    for y in years:
        if test(y):
            return int(y)
    return None


def parse_change_periods(text: str, dates: pd.Series) -> Optional[dict]:
    """Find the two periods named in the question. Returns dict or None."""
    low = text.lower()
    d = dates.dropna()
    if d.empty:
        return None
    # "2023 vs 2024"
    m = re.search(r"\b(20\d{2})\s*(?:vs\.?|versus|compared (?:to|with)|against|and|to)\s*(20\d{2})\b", low)
    if m:
        y1, y2 = int(m.group(1)), int(m.group(2))
        a, b = sorted((y1, y2))
        return {"base": (pd.Timestamp(a, 1, 1), pd.Timestamp(a, 12, 31, 23, 59, 59)), "base_label": str(a),
                "focus": (pd.Timestamp(b, 1, 1), pd.Timestamp(b, 12, 31, 23, 59, 59)), "focus_label": str(b),
                "note": f"Comparing {a} with {b}."}
    # quarter
    m = re.search(r"\bq([1-4])\b(?:\s*(?:of\s*)?(20\d{2}))?", low)
    if m:
        q = int(m.group(1))
        y = int(m.group(2)) if m.group(2) else _latest_year_with(d, lambda yy: ((d.dt.year == yy) & (d.dt.quarter == q)).any())
        if y is None:
            return None
        by, bq = (y, q - 1) if q > 1 else (y - 1, 4)
        return {"base": _quarter_range(by, bq), "base_label": f"Q{bq} {by}", "focus": _quarter_range(y, q), "focus_label": f"Q{q} {y}",
                "note": f"Comparing Q{q} {y} with the quarter before it (Q{bq} {by})."}
    # month name (+ optional year); 'may' only counts with a year or a preposition before it
    names = {"january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3, "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6,
             "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sept": 9, "sep": 9, "october": 10, "oct": 10,
             "november": 11, "nov": 11, "december": 12, "dec": 12}
    for mm in re.finditer(r"\b(" + "|".join(sorted(names, key=len, reverse=True)) + r")\b(?:\s*,?\s*(20\d{2}))?", low):
        num = names[mm.group(1)]
        if mm.group(1) == "may" and not (mm.group(2) or re.search(r"\b(in|during|of|for|from|since|by)\s+may\b", low)):
            continue
        y = int(mm.group(2)) if mm.group(2) else _latest_year_with(d, lambda yy, n=num: ((d.dt.year == yy) & (d.dt.month == n)).any())
        if y is None:
            continue
        by, bm = _shift_month(y, num, -1)
        return {"base": _month_range(by, bm), "base_label": pd.Timestamp(by, bm, 1).strftime("%b %Y"),
                "focus": _month_range(y, num), "focus_label": pd.Timestamp(y, num, 1).strftime("%b %Y"),
                "note": f"Comparing {pd.Timestamp(y, num, 1):%b %Y} with the month before it."}
    return None


def default_change_periods(dates: pd.Series) -> Optional[dict]:
    d = dates.dropna()
    if d.empty:
        return None
    mn, mx = d.min(), d.max()
    months = pd.period_range(mn.to_period("M"), mx.to_period("M"), freq="M")
    ok = list(months)
    dense = d.dt.normalize().nunique() >= len(months) * 3
    if dense and len(ok) >= 3:
        if mn > ok[0].start_time + pd.Timedelta(days=3):
            ok = ok[1:]
        if mx < ok[-1].end_time.normalize() - pd.Timedelta(days=3):
            ok = ok[:-1]
    elif len(ok) >= 2 and not dense:
        pass
    if len(ok) >= 2:
        b, f = ok[-2], ok[-1]
        return {"base": (b.start_time, b.end_time), "base_label": b.strftime("%b %Y"), "focus": (f.start_time, f.end_time), "focus_label": f.strftime("%b %Y"),
                "note": f"No period named, so I compared the latest complete month ({f.strftime('%b %Y')}) with the one before it ({b.strftime('%b %Y')})."}
    span = (mx - mn).days + 1
    if span >= 14:
        mid = mn + (mx - mn) / 2
        return {"base": (mn, mid.floor("D") + pd.Timedelta(hours=23, minutes=59, seconds=59)), "base_label": "first half",
                "focus": (mid.floor("D") + pd.Timedelta(days=1), mx + pd.Timedelta(hours=23, minutes=59, seconds=59)), "focus_label": "second half",
                "note": "No period named and under two complete months of data, so I compared the first half of the data with the second half."}
    return None


# ---------------------------------------------------------------------------------------------
# planning
# ---------------------------------------------------------------------------------------------
class PlanError(ValueError):
    pass


def _finish_spec(spec: ObjectiveSpec, schema: Schema, df: pd.DataFrame, text: str) -> ObjectiveSpec:
    """Shared tail: aggregation, direction, change periods, assumptions."""
    if spec.measure and spec.kind not in ("relationship", "target"):
        agg, why, explicit = _agg_from_text(text, spec.measure)
        if spec.planner == "rules" or explicit or spec.agg not in AGGS:
            spec.agg = agg
        spec.assumptions.append(why if spec.agg == agg else f"Using '{spec.agg}' as suggested by the AI plan.")
    if spec.kind == "compare":
        low = text.lower()
        wants_low = any(w in low for w in _LOW_WORDS)
        if spec.measure and lower_is_better(spec.measure) and any(w in low for w in _BAD_GOOD_FLIP):
            # for 'cost'/'wait'-like measures, 'worst' means HIGHEST and 'best' means lowest
            wants_low = "best" in low and "worst" not in low
            spec.assumptions.append(f"'{spec.measure}' is something you want LOW, so 'worst' is read as highest and 'best' as lowest.")
        spec.direction = "low" if wants_low else "high"
    if spec.kind == "change" and schema.date:
        per = parse_change_periods(text, df[schema.date]) or default_change_periods(df[schema.date])
        if per:
            spec.base_range, spec.focus_range = per["base"], per["focus"]
            spec.base_label, spec.focus_label = per["base_label"], per["focus_label"]
            spec.assumptions.append(per["note"])
    return spec


def plan_objective(text: str, prepared: PreparedFrame, obj_id: str = "o1", llm_call: Optional[Callable] = None) -> ObjectiveSpec:
    """Plan one objective. Tries the LLM planner when `llm_call` is given, falls back to rules."""
    text = (text or "").strip()
    if not text:
        raise PlanError("Write your question first.")
    schema, df = prepared.schema, prepared.df
    if llm_call is not None:
        try:
            spec = plan_with_llm(text, prepared, llm_call, obj_id)
            return _finish_spec(spec, schema, df, text)
        except Exception:
            pass          # any LLM/validation failure -> deterministic planner below
    spec = ObjectiveSpec(id=obj_id, text=text, kind=_detect_kind(text))
    meas = _match_columns(text, schema.measures)
    dims = _match_columns(text, schema.dimensions)
    flags = _match_columns(text, [c for c, i in schema.columns.items() if i.role == "flag"])
    # a dimension named after a 'by/per/each/across' phrase wins
    def _after_by(c):
        toks = re.sub(r"[^a-z0-9]+", " ", c.lower()).split()
        return bool(toks) and bool(re.search(rf"\b(by|per|each|across|among|within)\s+(?:\w+\s+)?{re.escape(toks[0])}", text.lower()))
    pref = [c for c, _, _ in dims if _after_by(c)]
    if pref:
        spec.dimension = pref[0]
    elif dims:
        spec.dimension = dims[0][0]
    if spec.kind in ("target", "relationship"):
        picks = [m[0] for m in sorted(meas[:2], key=lambda r: r[2])]
        if spec.kind == "target":
            tgt_words = ("budget", "target", "plan", "quota", "forecast", "goal", "allocation")
            tgt = next((c for c in schema.measures if col_words(c) & set(tgt_words)), None)
            act = next((c for c in picks if c != tgt), None)
            if act is None:
                for words in ({"actual", "actuals"}, {"spent", "spend", "expense", "expenses", "cost", "costs"}):
                    act = next((c for c in schema.measures if col_words(c) & words and c != tgt), None)
                    if act:
                        break
            spec.measure, spec.measure2 = act, tgt
            if act and tgt:
                spec.assumptions.append(f"Reading '{act}' as the actual figure and '{tgt}' as the target/budget.")
        else:
            if len(picks) >= 2:
                spec.measure, spec.measure2 = picks[0], picks[1]
                spec.assumptions.append(f"Measuring how '{picks[1]}' relates to '{picks[0]}' (which one is 'the cause' is your call; the maths is symmetric).")

    if spec.kind == "overview" and spec.dimension and re.search(r"\b(by|per|for each|across|among)\b", text.lower()):
        spec.kind = "compare"
        spec.assumptions.append(f"You asked for a figure split by '{spec.dimension}', so I compared its groups.")
    matched_anything = bool(meas or dims or spec.kind != "overview")
    if spec.measure is None:
        if meas:
            spec.measure = meas[0][0]
        elif schema.measures:
            # nothing named: most "complete" measure
            best = max(schema.measures, key=lambda c: (1 - schema.columns[c].missing_pct / 100, df[c].abs().sum(skipna=True)))
            spec.measure = best
            spec.assumptions.append(f"You did not name a measure, so I used '{best}' (the most complete numeric column). Change it if you meant another.")
    if spec.kind in ("compare", "composition") and spec.dimension is None and schema.dimensions:
        spec.dimension = schema.dimensions[0]
        spec.assumptions.append(f"You did not name a grouping, so I used '{spec.dimension}'.")
    spec.planner = "rules"
    if not matched_anything:
        spec.assumptions.insert(0, "I could not match your wording to specific columns or a type of question, so this is a general overview. Rephrase or pick the analysis type yourself.")
    return _finish_spec(spec, schema, df, text)


def override_spec(spec: ObjectiveSpec, prepared: PreparedFrame, **changes) -> ObjectiveSpec:
    """Apply the user's own corrections (kind, measure, measure2, dimension, agg). Validated against the real schema;
    unknown values raise PlanError so a bad choice can never silently change an answer."""
    import dataclasses
    schema = prepared.schema
    allowed = {"kind", "measure", "measure2", "dimension", "agg"}
    clean = {k: v for k, v in changes.items() if k in allowed and v not in (None, "")}
    bad = set(changes) - allowed
    if bad:
        raise PlanError(f"Cannot change: {', '.join(sorted(bad))}")
    if "kind" in clean and clean["kind"] not in ANALYSES:
        raise PlanError(f"Unknown analysis type '{clean['kind']}'.")
    if "agg" in clean and clean["agg"] not in AGGS:
        raise PlanError(f"Unknown aggregation '{clean['agg']}'.")
    for k in ("measure", "measure2"):
        if k in clean and clean[k] not in schema.measures:
            raise PlanError(f"'{clean[k]}' is not a number column.")
    if "dimension" in clean and clean["dimension"] not in schema.dimensions:
        raise PlanError(f"'{clean['dimension']}' is not a grouping column.")
    new = dataclasses.replace(spec, **clean, assumptions=list(spec.assumptions))
    new.planner = "you"
    if clean:
        new.assumptions.append("You adjusted: " + ", ".join(f"{k} = {v}" for k, v in clean.items()) + ".")
    if new.kind in ("compare", "composition") and not new.dimension and schema.dimensions:
        new.dimension = schema.dimensions[0]
    if new.kind in ("target", "relationship") and not new.measure2:
        others = [m for m in schema.measures if m != new.measure]
        new.measure2 = others[0] if others else None
    if new.kind == "change" and schema.date and not (new.base_range and new.focus_range):
        per = parse_change_periods(new.text, prepared.df[schema.date]) or default_change_periods(prepared.df[schema.date])
        if per:
            new.base_range, new.focus_range = per["base"], per["focus"]
            new.base_label, new.focus_label = per["base_label"], per["focus_label"]
    return new


def plan_with_llm(text: str, prepared: PreparedFrame, llm_call: Callable, obj_id: str = "o1") -> ObjectiveSpec:
    """Ask an LLM for a plan. Only column NAMES and ROLES are sent (no cell values). The reply is
    validated against the real schema; anything invalid raises PlanError."""
    s = prepared.schema
    cols = [{"name": c, "role": i.role} for c, i in s.columns.items() if i.role in ("measure", "dimension", "date", "flag")]
    prompt = (
        "You plan data analyses. Choose ONE analysis for the user's question using ONLY the columns listed.\n"
        f"Columns: {json.dumps(cols)}\nQuestion: {text}\n"
        f"Reply with JSON only: {{\"kind\": one of {list(KINDS)}, \"measure\": column or null, \"measure2\": column or null, "
        f"\"dimension\": column or null, \"agg\": one of {list(AGGS)}}}. "
        "kind=target needs measure (actual) and measure2 (target); kind=relationship needs measure and measure2; "
        "kind=compare and composition need measure and dimension; trend and change need measure."
    )
    raw = llm_call(prompt)
    return parse_llm_plan(raw, prepared, text, obj_id)


def parse_llm_plan(raw: str, prepared: PreparedFrame, text: str, obj_id: str = "o1") -> ObjectiveSpec:
    s = prepared.schema
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        raise PlanError("No JSON in LLM reply")
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        raise PlanError(f"Invalid JSON: {e}")
    kind = d.get("kind")
    if kind not in KINDS:
        raise PlanError(f"Unknown kind {kind!r}")
    def pick(key, allowed):
        v = d.get(key)
        if v in (None, "", "null"):
            return None
        if v not in allowed:
            raise PlanError(f"{key}={v!r} is not a valid column")
        return v
    measure, measure2 = pick("measure", s.measures), pick("measure2", s.measures)
    dimension = pick("dimension", s.dimensions)
    agg = d.get("agg") if d.get("agg") in AGGS else "sum"
    need = {"target": (measure, measure2), "relationship": (measure, measure2), "compare": (measure, dimension),
            "composition": (measure, dimension), "trend": (measure,), "change": (measure,), "distribution": (measure,), "overview": (measure,)}[kind]
    if not all(need):
        raise PlanError("LLM plan is missing required columns for its kind")
    if kind in ("trend", "change") and not s.date:
        raise PlanError("No date column")
    spec = ObjectiveSpec(id=obj_id, text=text, kind=kind, measure=measure, measure2=measure2, dimension=dimension, agg=agg, planner="llm")
    spec.assumptions.append("This plan was suggested by AI from your column names (no data values were sent). Check it before relying on it.")
    return spec


def parse_llm_dashboard(raw: str, prepared: PreparedFrame, text: str, base_id: str = "o1") -> dict:
    """Validate a multi-KPI + multi-chart AI blueprint against the real schema.

    Returns {"kpis": [...], "specs": [ObjectiveSpec, ...]}.
    Raises PlanError if JSON is invalid or yields zero valid analyses.
    """
    s = prepared.schema
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        raise PlanError("No JSON object in LLM dashboard plan")
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        raise PlanError(f"Invalid JSON in LLM dashboard plan: {e}")

    entity_cols = set(s.dimensions) | set(s.ids)
    meas_cols = set(s.measures)

    valid_kpis, seen_kpis = [], set()
    for item in (d.get("kpis") or [])[:8]:
        if not isinstance(item, dict):
            continue
        col = item.get("col")
        k_type = item.get("type", "measure")
        agg = item.get("agg", "sum")
        label = str(item.get("label") or "").strip()[:50]
        if k_type == "distinct" or agg == "nunique":
            if col in entity_cols and ("distinct", col) not in seen_kpis:
                seen_kpis.add(("distinct", col))
                valid_kpis.append({"type": "distinct", "col": col, "agg": "nunique", "label": label or f"Unique {col}"})
        elif col in meas_cols:
            if agg not in AGGS:
                agg = default_agg(col)
            if ("measure", col, agg) not in seen_kpis:
                seen_kpis.add(("measure", col, agg))
                valid_kpis.append({"type": "measure", "col": col, "agg": agg, "label": label})

    valid_specs, seen_specs = [], set()
    for idx, item in enumerate((d.get("analyses") or [])[:4], 1):
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        if kind not in KINDS:
            continue
        measure = item.get("measure") if item.get("measure") in meas_cols else None
        measure2 = item.get("measure2") if item.get("measure2") in meas_cols else None
        dimension = item.get("dimension") if item.get("dimension") in s.dimensions else None
        agg = item.get("agg") if item.get("agg") in AGGS else (default_agg(measure) if measure else "sum")
        direction = "low" if item.get("direction") == "low" else "high"
        title = str(item.get("title") or text).strip()[:90]

        if kind in ("trend", "change") and not s.date:
            continue
        need = {
            "target": (measure, measure2),
            "relationship": (measure, measure2),
            "compare": (measure, dimension),
            "composition": (measure, dimension),
            "trend": (measure,),
            "change": (measure,),
            "distribution": (measure,),
            "overview": (measure,),
        }[kind]
        if not all(need):
            continue
        sig = (kind, measure, measure2, dimension, agg)
        if sig in seen_specs:
            continue
        seen_specs.add(sig)
        sp = ObjectiveSpec(
            id=f"{base_id}_{idx}" if idx > 1 else base_id,
            text=title,
            kind=kind,
            measure=measure,
            measure2=measure2,
            dimension=dimension,
            agg=agg,
            direction=direction,
            top_n=10,
            planner="llm",
        )
        sp.assumptions.append("Planned by Gemini AI from your column schema (zero data rows sent).")
        if kind == "change" and s.date:
            per = parse_change_periods(text, prepared.df[s.date]) or default_change_periods(prepared.df[s.date])
            if per:
                sp.base_range, sp.focus_range = per["base"], per["focus"]
                sp.base_label, sp.focus_label = per["base_label"], per["focus_label"]
                sp.assumptions.append(per["note"])
        valid_specs.append(sp)

    if not valid_specs and not valid_kpis:
        raise PlanError("LLM plan produced no valid KPIs or analyses for this schema")
    return {"kpis": valid_kpis, "specs": valid_specs}


def plan_dashboard_with_llm(text: str, prepared: PreparedFrame, llm_call: Callable, base_id: str = "o1") -> dict:
    """Ask an LLM to turn a free-form business objective into validated KPI cards + charts.

    Only column NAMES and ROLES are sent (no data values). Every returned field is schema-checked.
    """
    s = prepared.schema
    cols = [{"name": c, "role": i.role} for c, i in s.columns.items() if i.role in ("measure", "dimension", "date", "id", "flag")]
    prompt = (
        "You are an expert analytics architect. Given ONLY the user's objective and the table's column schema "
        "(no raw cell data), design the exact KPI cards and analytical charts that answer the objective.\n"
        f"Schema columns: {json.dumps(cols)}\n"
        f"User objective: {text}\n\n"
        "Return ONLY valid JSON matching:\n"
        "{\n"
        '  "kpis": [{"type": "measure"|"distinct", "col": exact_column_name, "agg": "sum"|"mean"|"median"|"count"|"nunique", "label": short_card_title}],\n'
        '  "analyses": [{"kind": one_of_' + json.dumps(list(KINDS)) + ', "title": concise_chart_title, '
        '"measure": measure_col, "measure2": measure_col_or_null, "dimension": dimension_col_or_null, '
        '"agg": "sum"|"mean"|"median"|"count", "direction": "high"|"low"}]\n'
        "}\n"
        "Rules:\n"
        "1. Extract EVERY KPI mentioned or directly needed (support 1 to 8 KPIs). Use type='distinct', agg='nunique' for counts like 'number of X'.\n"
        "2. Match 'Total X' with agg='sum' and 'Average X' with agg='mean' strictly per metric; never confuse metrics with different modifiers.\n"
        "3. Choose 1 to 4 diverse, non-duplicate charts that genuinely explore the user's objective. If user asks a specific comparison or trend, match that exact chart; if user lists metrics broadly, show trend over time + breakdowns across the most relevant dimensions.\n"
        "4. Column names MUST match exact strings from Schema columns. Never invent columns."
    )
    raw = llm_call(prompt)
    return parse_llm_dashboard(raw, prepared, text, base_id=base_id)


# ---------------------------------------------------------------------------------------------
# feasibility
# ---------------------------------------------------------------------------------------------
def check_feasibility(spec: ObjectiveSpec, prepared: PreparedFrame) -> Feasibility:
    s, df = prepared.schema, prepared.df
    fe = Feasibility()

    def block(msg, structural=True):
        fe.status = "blocked"
        fe.structural = structural
        fe.reasons.append(msg)
        return fe

    if spec.kind not in KINDS:
        return block(f"Unknown analysis type '{spec.kind}'.")
    if not spec.measure:
        return block("I could not tell which number column your question is about. Pick one in the plan.")
    for c in (spec.measure, spec.measure2, spec.dimension):
        if c and c not in df.columns:
            return block(f"Column '{c}' is not in the data.")
    if spec.kind in ("trend", "change") and not s.date:
        return block("This question is about time, but the file has no date column I could read.")
    if spec.kind in ("compare", "composition") and not spec.dimension:
        return block("This question needs a grouping column (for example region or category) and I could not find one.")
    if spec.kind == "target" and not (spec.measure and spec.measure2):
        return block("This is about actual versus a budget/target, but I could not find both an actual column and a budget/target column in the file.")
    if spec.kind == "relationship" and not spec.measure2:
        return block("A relationship needs two number columns and I could only find one in your question.")
    if spec.kind == "change" and not (spec.base_range and spec.focus_range):
        return block("I could not work out which two periods to compare. Name them in your question (for example 'Q3 vs Q2' or 'June 2024').")
    if spec.kind == "change" and spec.base_range and spec.focus_range and spec.base_range == spec.focus_range:
        return block("The two periods are identical.")
    needed = spec.needed_columns(s)
    d = df[needed].dropna()
    if len(d) < 8:
        return block(f"Only {len(d)} row(s) have every column this question needs ({', '.join(needed)}), which is too few for a reliable answer.", structural=False)
    if spec.kind in ("compare", "composition") and df[spec.dimension].nunique(dropna=True) < 2:
        return block(f"'{spec.dimension}' has only one group, so there is nothing to compare.")
    if spec.kind in ("trend",):
        tbl, grain = period_table(d.rename(columns={spec.measure: spec.measure}), s.date, spec.measure, "sum")
        if (~tbl["partial"] & tbl["value"].notna()).sum() < 3:
            fe.status = "caution"
            fe.reasons.append("Fewer than 3 complete time periods, so any trend would be weak.")
    gate = assess_gate(df, needed, s.date)
    fe.gate = gate
    if STATUS_ORDER[gate.level] > STATUS_ORDER[fe.status]:
        fe.status = gate.level
    fe.reasons.extend(gate.reasons)
    if fe.status == "decision":
        fe.reasons.append("Decide how to handle the missing values (or continue anyway) before running this question.")
    if fe.status == "blocked":
        fe.reasons.append("So much of the needed data is missing that the answer would be unreliable. You can still run it, but treat the result with great caution.")
    return fe


# ---------------------------------------------------------------------------------------------
# handling / derivation applied to the prepared frame
# ---------------------------------------------------------------------------------------------
_ROLE_WORDS = {
    "revenue": {"revenue", "sales", "income", "turnover", "takings"}, "cost": {"cost", "costs", "cogs", "expense", "expenses"},
    "profit": {"profit", "earnings"}, "quantity": {"quantity", "qty", "units"}, "unit_price": {"price", "unit_price"},
    "budget": {"budget", "plan", "target"}, "actual": {"actual", "actuals"}, "variance": {"variance", "diff", "difference"},
}


_PCT_WORDS = {"pct", "percent", "percentage", "ratio", "rate", "margin", "growth", "change"}


def infer_relation_roles(schema: Schema) -> dict:
    """Map semantic roles to columns, only when the match is unambiguous (exactly one candidate)."""
    roles = {}
    for role, words in _ROLE_WORDS.items():
        cands = [c for c in schema.measures if col_words(c) & words and not (col_words(c) & _PCT_WORDS) and "%" not in str(c)]
        if role == "unit_price":
            cands = [c for c in cands if not (col_words(c) & {"total"})]
        if len(cands) == 1:
            roles[role] = cands[0]
    # a column cannot play two roles
    seen = {}
    for r, c in list(roles.items()):
        if c in seen:
            roles.pop(r)
            roles.pop(seen[c], None)
        else:
            seen[c] = r
    return roles


@dataclass
class HandlingResult:
    prepared: PreparedFrame
    log: list = field(default_factory=list)
    identity_report: list = field(default_factory=list)
    estimated_cells: dict = field(default_factory=dict)
    derived_cells: dict = field(default_factory=dict)


def apply_handling(prepared: PreparedFrame, policies: Optional[dict] = None, derive: bool = True) -> HandlingResult:
    """Exact derivations first, then the user's per-column choices. Original frame is not modified."""
    df = prepared.df
    out = HandlingResult(prepared=prepared)
    if derive:
        roles = infer_relation_roles(prepared.schema)
        if len(roles) >= 2:
            # only trust a relation that actually holds on rows where everything is measured
            from data_quality import DEFAULT_RELATIONS
            checks = {c["relation"]: c for c in check_identities(df, roles)}
            trusted = []
            for rel in DEFAULT_RELATIONS:
                c = checks.get(rel.name)
                if c is None:
                    continue
                if c["checked_rows"] >= 5 and c["violation_pct"] <= 5.0:
                    trusted.append(rel)
                else:
                    out.log.append(f"Not filling from '{rel.name}': it holds on only {100 - c['violation_pct']:.0f}% of the {c['checked_rows']} rows where all columns exist (or too few rows to verify)")
            dres = derive_missing(df, roles, relations=tuple(trusted))
            df = dres.df
            out.log.extend(dres.log)
            out.identity_report = dres.identity_report
            out.derived_cells = {c: int(m.sum()) for c, m in dres.derived_masks.items()}
            for it in dres.identity_report:
                if it["violations"]:
                    out.log.append(f"Check: {it['violations']} of {it['checked_rows']} row(s) break '{it['relation']}' (possible data error)")
    if policies:
        pres = apply_policies(df, policies)
        if pres.rows_dropped:
            dropped = df[~df.index.isin(pres.df.index)].copy()
            dropped["quarantine_reason"] = "Removed at your request (missing value)"
            q = pd.concat([prepared.quarantine, dropped], ignore_index=True)
        else:
            q = prepared.quarantine
        df = pres.df
        out.log.extend(pres.log)
        out.estimated_cells = {c: int(m.sum()) for c, m in pres.filled_masks.items()}
    else:
        q = prepared.quarantine
    new = PreparedFrame(df=df.reset_index(drop=True), schema=prepared.schema, log=list(prepared.log) + out.log, quarantine=q)
    out.prepared = new
    return out


# ---------------------------------------------------------------------------------------------
# running
# ---------------------------------------------------------------------------------------------
@dataclass
class ObjectiveResult:
    spec: ObjectiveSpec
    feasibility: Feasibility
    finding: Optional[Finding]


def run_objective(spec: ObjectiveSpec, prepared: PreparedFrame, currency: str = "", accept_risk: bool = False) -> ObjectiveResult:
    fe = check_feasibility(spec, prepared)
    if fe.status == "blocked" and fe.structural:
        return ObjectiveResult(spec, fe, Finding(spec.id, spec.kind, spec.text, status="blocked", headline=fe.reasons[0], confidence="low"))
    if fe.status in ("decision", "blocked") and not accept_risk:
        return ObjectiveResult(spec, fe, Finding(spec.id, spec.kind, spec.text, status=fe.status,
                                                 headline="Waiting for your decision on missing data before this can be answered.", confidence="low"))
    try:
        finding = ANALYSES[spec.kind](prepared.df, prepared.schema, spec, currency)
    except Exception as e:          # one bad question must never take the others down
        finding = Finding(spec.id, spec.kind, spec.text, status="error", headline=f"This question could not be analysed ({type(e).__name__}: {e}).", confidence="low")
        return ObjectiveResult(spec, fe, finding)
    if fe.status in ("caution", "decision", "blocked") or (fe.gate and fe.gate.level != "ok"):
        finding.caveats = list(dict.fromkeys(list(fe.reasons) + finding.caveats))
        if finding.status == "ok":
            finding.status = "caution"
    return ObjectiveResult(spec, fe, finding)


def run_objectives(specs: list, prepared: PreparedFrame, currency: str = "", accept_risk_ids: Optional[set] = None) -> list:
    accept = accept_risk_ids or set()
    return [run_objective(sp, prepared, currency, sp.id in accept) for sp in specs]


def suggest_objectives(prepared: PreparedFrame, limit: int = 6) -> list:
    """Starter questions built from the actual columns (all answerable by the engine)."""
    s, df = prepared.schema, prepared.df
    ms = sorted(s.measures, key=lambda c: (s.columns[c].missing_pct, -float(df[c].abs().sum(skipna=True))))[:3]
    out = []
    if not ms:
        return out
    m = ms[0]
    if s.date:
        out.append(f"How has {m} changed over time?")
        out.append(f"Why did {m} change between the last two months?")
    for dim in s.dimensions[:1]:
        out.append(f"Which {dim} has the highest {m}?")
        out.append(f"What share of {m} comes from each {dim}?")
    if len(ms) >= 2:
        out.append(f"Is {ms[0]} related to {ms[1]}?")
    out.append(f"Are there unusual values in {m}?")
    return out[:limit]

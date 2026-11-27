"""Objective-driven analysis screen. Rendered by app.py when the user picks 'Ask your own questions'.

Flow: data check -> missing-data decisions -> add questions -> answers (with plan, caveats, deck download).
All numbers come from deterministic code (analyses.py); nothing here invents figures.
"""
import hashlib
import html
import re
import tempfile
from typing import Optional

import pandas as pd
import streamlit as st

import analyses as an
import objectives as ob
from objective_charts import figure_for
from data_quality import missing_profile
from schema import prepare_frame


def _h(val):
    return html.escape(str(val)) if val is not None else ""

STATUS_LABEL = {"ok": "Answered", "caution": "Answered, read the notes", "decision": "Needs your decision",
                "blocked": "Cannot answer", "error": "Error"}
KIND_LABEL = {"trend": "Trend over time", "compare": "Compare groups", "change": "What changed between periods",
              "target": "Actual vs budget/target", "relationship": "Relationship between two numbers",
              "composition": "Share of the total", "distribution": "Spread & unusual values", "overview": "Overview"}
AGG_LABEL = {"sum": "Add up (total)", "mean": "Average", "median": "Median (typical value)", "count": "Count of records"}

MEASURE_CHOICES = {
    "Leave blank (recommended)": {"method": "keep"},
    "Remove those rows": {"method": "drop_rows"},
    "Fill with the median": {"method": "fill_median"},
    "Fill with the average": {"method": "fill_mean"},
    "Fill with zero": {"method": "fill_zero"},
}
OTHER_CHOICES = {
    "Leave blank (recommended)": {"method": "keep"},
    "Remove those rows": {"method": "drop_rows"},
    "Fill with 'Unknown'": {"method": "fill_value", "value": "Unknown"},
}


@st.cache_data(show_spinner=False, max_entries=4)
def _prepare(_df, sig: str):
    return prepare_frame(_df)


def _sig(df: pd.DataFrame) -> str:
    return hashlib.md5(pd.util.hash_pandas_object(df, index=True).values.tobytes() + "|".join(map(str, df.columns)).encode()).hexdigest()[:16]


def _state_reset_if_new(sig: str):
    if st.session_state.get("oq_sig") != sig:
        st.session_state["oq_sig"] = sig
        st.session_state["oq_questions"] = []
        st.session_state["oq_next"] = 1
        st.session_state["oq_accept"] = set()
        st.session_state["oq_over"] = {}
        st.session_state["oq_ai_plans"] = {}
        st.session_state["oq_ai_briefings"] = {}
        st.session_state.pop("oq_deck", None)


def _plan_smart(prep, q, sig: str, api_key: str = None, consume_ai_fn=None):
    """Plan with Gemini AI when api_key is set and budget allows (cached per question+schema), else rules."""
    if api_key:
        cache = st.session_state.setdefault("oq_ai_plans", {})
        k_hash = hashlib.md5(api_key.encode()).hexdigest()[:8]
        ckey = (sig, q["id"], q["text"], k_hash)
        if ckey not in cache and (consume_ai_fn is None or consume_ai_fn()):
            try:
                from ai_narrator import make_gemini_json_caller
                caller = make_gemini_json_caller(api_key)
                bp = ob.plan_dashboard_with_llm(q["text"], prep, caller, base_id=q["id"])
                cache[ckey] = bp
            except Exception:
                cache[ckey] = None
        bp = cache.get(ckey)
        if bp and bp.get("specs"):
            specs = list(bp["specs"])
            over = st.session_state["oq_over"].get(q["id"])
            if over and specs:
                try:
                    specs[0] = ob.override_spec(specs[0], prep, **over)
                except ob.PlanError:
                    pass
            return list(bp.get("kpis") or []), specs, None

    spec, err = _plan(prep, q)
    if err:
        return [], [], err
    return [], [spec], None


def _add_question(text: str):
    text = (text or "").strip()
    if not text:
        return
    if any(q["text"].lower() == text.lower() for q in st.session_state["oq_questions"]):
        return
    n = st.session_state["oq_next"]
    st.session_state["oq_next"] = n + 1
    st.session_state["oq_questions"].append({"id": f"o{n}", "text": text})
    st.session_state.pop("oq_deck", None)


def _remove_question(qid: str):
    st.session_state["oq_questions"] = [q for q in st.session_state["oq_questions"] if q["id"] != qid]
    st.session_state["oq_over"].pop(qid, None)
    st.session_state["oq_accept"].discard(qid)
    st.session_state.pop("oq_deck", None)


# ------------------------------------------------------------------------------------------------
def _section_data(prep):
    s = prep.schema
    st.subheader("1. Your data")
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", f"{len(prep.df):,}")
    c2.metric("Columns", f"{len(prep.df.columns):,}")
    c3.metric("Date column", s.date or "none found")
    rows = [{"Column": n, "I read it as": {"measure": "number", "dimension": "category", "date": "date", "id": "ID",
                                              "flag": "yes/no", "text": "free text"}.get(i.role, i.role),
             "Blank %": round(i.missing_pct, 1), "Note": i.note} for n, i in s.columns.items()]
    with st.expander("How I read each column", expanded=False):
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if prep.log:
        with st.expander(f"What I cleaned automatically ({len(prep.log)})", expanded=False):
            for line in prep.log:
                st.write("• " + line)
    if prep.quarantine is not None and len(prep.quarantine):
        st.caption(f"{len(prep.quarantine)} row(s) were set aside (for example total rows or exact duplicates) so they do not distort the numbers.")


def _section_missing(prep, sig):
    """Returns (policies, derive_flag)."""
    s, df = prep.schema, prep.df
    st.subheader("2. Missing data")
    prof = missing_profile(df, [c for c in df.columns if c not in s.ids], s.date)
    miss = prof[prof["missing_n"] > 0]
    if miss.empty:
        st.success("No blank values in the columns that matter. Nothing to decide here.")
        return {}, True
    worst = float(miss["missing_pct"].max())
    msg = f"{len(miss)} column(s) have blanks; the worst has {worst:.0f}% blank."
    (st.error if worst >= 40 else st.warning if worst >= 20 else st.info)(msg)
    show = miss[["column", "missing_n", "missing_pct", "pattern_detail"]].rename(
        columns={"column": "Column", "missing_n": "Blank rows", "missing_pct": "Blank %", "pattern_detail": "Pattern"})
    st.dataframe(show, use_container_width=True, hide_index=True)
    derive = st.checkbox("Fill blanks that can be calculated exactly (for example profit = revenue − cost)", value=True,
                         key=f"oq_derive_{sig}",
                         help="Only used when the relationship really holds in your complete rows. These cells are marked as calculated.")
    st.caption("Choose what to do per column. 'Leave blank' is safest: each answer then uses only rows where its columns exist and tells you the coverage. "
               "Filled values are estimates and will be labelled as such.")
    policies = {}
    for _, r in miss.iterrows():
        c = r["column"]
        is_meas = s.role_of(c) == "measure"
        choices = MEASURE_CHOICES if is_meas else OTHER_CHOICES
        extra = ""
        if is_meas:
            ser = pd.to_numeric(df[c], errors="coerce").dropna()
            if len(ser) > 3 and ser.median() not in (0, None):
                extra = f"  (average {ser.mean():,.2f} vs median {ser.median():,.2f}" + (" — skewed, median is safer)" if abs(ser.mean() / ser.median() - 1) > 0.25 else ")")
        pick = st.selectbox(f"{c}: {int(r['missing_n'])} blank ({r['missing_pct']:.0f}%)" + extra, list(choices), key=f"oq_pol_{c}_{sig}")
        if choices[pick]["method"] != "keep":
            policies[c] = dict(choices[pick])
    return policies, derive


def _section_questions(prep):
    st.subheader("3. What do you want to find out?")
    st.caption("Ask in plain words, one question per line item. You can add several; each gets its own answer and its own slide.")
    with st.form("oq_form", clear_on_submit=True):
        text = st.text_input("Your question", placeholder="e.g. Why did revenue drop in the last quarter?  /  Which region performs worst?")
        if st.form_submit_button("➕ Add question", use_container_width=True):
            _add_question(text)
    sugg = [t for t in ob.suggest_objectives(prep) if t.lower() not in {q["text"].lower() for q in st.session_state["oq_questions"]}]
    if sugg:
        st.caption("Ideas based on your columns (click to add):")
        cols = st.columns(2)
        for i, t in enumerate(sugg[:6]):
            if cols[i % 2].button(t, key=f"oq_sugg_{i}_{abs(hash(t)) % 10**6}", use_container_width=True):
                _add_question(t)
                st.rerun()


def _plan(prep, q):
    try:
        spec = ob.plan_objective(q["text"], prep, q["id"])
        over = st.session_state["oq_over"].get(q["id"])
        if over:
            spec = ob.override_spec(spec, prep, **over)
        return spec, None
    except ob.PlanError as e:
        return None, str(e)


def _adjust_widget(prep, spec, qid):
    s = prep.schema
    sg = st.session_state.get("oq_sig", "")
    with st.expander("How I understood this (change it if wrong)"):
        kinds = list(KIND_LABEL)
        k = st.selectbox("Type of analysis", kinds, index=kinds.index(spec.kind) if spec.kind in kinds else 0,
                         format_func=KIND_LABEL.get, key=f"oq_k_{qid}_{sg}")
        meas = list(s.measures)
        m = st.selectbox("Main number", meas, index=meas.index(spec.measure) if spec.measure in meas else 0, key=f"oq_m_{qid}_{sg}") if meas else None
        m2 = None
        if k in ("target", "relationship") and len(meas) > 1:
            m2 = st.selectbox("Second number (budget / other number)", meas,
                              index=meas.index(spec.measure2) if spec.measure2 in meas else min(1, len(meas) - 1), key=f"oq_m2_{qid}_{sg}")
        dim = None
        if s.dimensions:
            dims = list(s.dimensions)
            dim = st.selectbox("Group by", dims, index=dims.index(spec.dimension) if spec.dimension in dims else 0, key=f"oq_d_{qid}_{sg}")
        aggs = list(AGG_LABEL)
        a = st.selectbox("How to combine values", aggs, index=aggs.index(spec.agg) if spec.agg in aggs else 0,
                         format_func=AGG_LABEL.get, key=f"oq_a_{qid}_{sg}")
        new = {"kind": k, "measure": m, "measure2": m2, "dimension": dim, "agg": a}
        cur = {"kind": spec.kind, "measure": spec.measure, "measure2": spec.measure2, "dimension": spec.dimension, "agg": spec.agg}
        changed = {x: v for x, v in new.items() if v is not None and v != cur.get(x)}
        if changed and st.button("Apply my changes", key=f"oq_apply_{qid}_{sg}"):
            st.session_state["oq_over"].setdefault(qid, {}).update(changed)
            st.session_state.pop("oq_deck", None)
            st.rerun()
        if qid in st.session_state["oq_over"] and st.button("Go back to my original wording", key=f"oq_undo_{qid}_{sg}"):
            st.session_state["oq_over"].pop(qid, None)
            st.session_state.pop("oq_deck", None)
            st.rerun()
        if spec.assumptions:
            st.markdown("**Assumptions I made**")
            for a_ in spec.assumptions:
                st.write("• " + a_)


def _render_result(prep, res, idx, currency, brand_color=None):
    f, spec = res.finding, res.spec
    with st.container(border=True):
        st.markdown(f"**Q{idx}. {spec.text}**")
        label = STATUS_LABEL.get(f.status, f.status)
        st.caption(f"{label}  ·  {KIND_LABEL.get(spec.kind, spec.kind)}  ·  confidence: {f.confidence}")
        if f.status in ("decision", "blocked") and not res.feasibility.structural:
            for r in res.feasibility.reasons:
                st.warning(r)
            if st.button("Answer anyway, I accept the risk", key=f"oq_acc_{spec.id}"):
                st.session_state["oq_accept"].add(spec.id)
                st.session_state.pop("oq_deck", None)
                st.rerun()
        elif f.status == "blocked":
            st.error(f.headline)
            for r in res.feasibility.reasons[1:]:
                st.write("• " + r)
        elif f.status == "error":
            st.error(f.headline)
        else:
            st.markdown(f"### {f.headline}")
            for d in f.details:
                st.write("• " + d)
            fig = figure_for(f, dark=True, brand_color=brand_color)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True, key=f"oq_fig_{spec.id}")
            if f.table is not None and len(f.table):
                with st.expander("See the numbers"):
                    st.dataframe(f.table.head(200), use_container_width=True, hide_index=True)
            for c in f.caveats:
                st.warning(c)
            st.caption(f"{f.n_rows:,} rows used · {f.coverage_pct:.0f}% of rows had the needed values")
        _adjust_widget(prep, spec, spec.id)
        if st.button("🗑 Remove this question", key=f"oq_rm_{spec.id}"):
            _remove_question(spec.id)
            st.rerun()


# ------------------------------------------------------------------------------------------------
def render_objectives(df: pd.DataFrame, source_notes=(), dataset_name: str = "Your data"):
    with st.sidebar:
        currency_symbol = st.selectbox("Currency Symbol", ["$", "₵", "₦", "£", "€", "None"], index=0, key="oq_curr")
        currency = "" if currency_symbol == "None" else currency_symbol
        brand_color = st.color_picker("Brand Accent Color", value="#6366F1", key="oq_brand")
        brand_name = st.text_input("Brand / Organization Name", value="", key="oq_brand_name")
        title = st.text_input("Deck title", value=f"{dataset_name} Analysis", key="oq_title")

    st.title("Ask your own questions")
    st.caption("State what you want to learn. I plan the analysis, check the data can support it, and answer each question with the numbers, charts and caveats.")
    if df is None or df.empty:
        st.warning("This file has no rows to analyse.")
        return
    sig = _sig(df)
    _state_reset_if_new(sig)
    try:
        prep = _prepare(df, sig)
    except Exception as e:
        st.error(f"Could not read this file's structure: {e}")
        return
    if not prep.schema.measures:
        st.error("I could not find any number columns in this file, so there is nothing to calculate. Check that your amounts are in their own columns.")
        _section_data(prep)
        return

    _section_data(prep)
    policies, derive = _section_missing(prep, sig)
    try:
        handled = ob.apply_handling(prep, policies, derive)
    except Exception as e:
        st.error(f"Could not apply your missing-data choices: {e}")
        return
    hp = handled.prepared
    notes = [n for n in handled.log if n]
    if notes:
        with st.expander(f"What these choices changed ({len(notes)})"):
            for n in notes:
                st.write("• " + n)
    if handled.estimated_cells:
        st.info("Filled values are estimates: " + ", ".join(f"{c} ({n} cells)" for c, n in handled.estimated_cells.items()) + ". Answers using them say so.")
    if len(hp.df) == 0:
        st.error("Your choices removed every row. Pick a gentler option for at least one column.")
        return

    prev_q_count = len(st.session_state.get("oq_questions", []))
    _section_questions(hp)
    qs = st.session_state["oq_questions"]
    if prev_q_count == 0 and len(qs) > 0:
        st.rerun()
    st.subheader("4. Answers")
    if not qs:
        st.info("Add at least one question above, or click one of the ideas.")
        return
    specs, errors = [], []
    for q in qs:
        spec, err = _plan(hp, q)
        (specs.append(spec) if spec else errors.append((q, err)))
    for q, err in errors:
        st.error(f"'{q['text']}': {err}")
    results = ob.run_objectives(specs, hp, currency, st.session_state["oq_accept"])
    for i, r in enumerate(results, 1):
        _render_result(hp, r, i, currency, brand_color=brand_color)

    # ---- outputs
    st.subheader("5. Take it with you")
    answered = [r for r in results if r.finding.status in ("ok", "caution")]
    deck_key = (sig, tuple((r.spec.id, r.spec.text, r.finding.headline) for r in results), title, brand_color, brand_name, currency)
    if not answered:
        st.caption("Answer at least one question to build a deck.")
    elif st.session_state.get("oq_deck", {}).get("key") == deck_key:
        st.download_button("📥 Download slide deck (.pptx)", st.session_state["oq_deck"]["bytes"], file_name="Analysis_Report.pptx",
                           mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                           use_container_width=True, key="oq_dl_deck")
    elif st.button("📊 Prepare slide deck", use_container_width=True, key="oq_prep_deck"):
        try:
            from objective_deck import build_objective_deck
            with st.spinner("Building slides..."):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    path = build_objective_deck(
                        results, title=title, quality_notes=hp.log, brand_color=brand_color,
                        brand_name=brand_name or None, output_dir=tmp_dir,
                    )
                    with open(path, "rb") as fh:
                        st.session_state["oq_deck"] = {"key": deck_key, "bytes": fh.read()}
            st.rerun()
        except Exception as e:
            st.error(f"Could not build the slide deck: {e}")
    from export_utils import sanitize_df_for_export
    csv_bytes = sanitize_df_for_export(hp.df).to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 Download the cleaned data (.csv)", csv_bytes,
                       file_name="cleaned_data.csv", mime="text/csv", use_container_width=True, key="oq_dl_csv")


# ================================================================================================
# UNIFIED 3-TAB DASHBOARD & STUDIO HELPERS (Used by app.py)
# ================================================================================================
def _format_measure_value(col: str, val, currency: str) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "n/a"
    words = an.col_words(col)
    if (words & {"margin", "pct", "percent"}) or "%" in str(col):
        pct_val = val * 100.0 if abs(val) <= 1.0 else val
        return f"{pct_val:.1f}%"
    pre = currency if an.is_money(col) else ""
    a = abs(float(val))
    sign = "-" if val < 0 else ""
    if a >= 1e12:
        return f"{sign}{pre}{a / 1e12:.2f}T"
    if a >= 1e9:
        return f"{sign}{pre}{a / 1e9:.2f}B"
    if a >= 1e6:
        return f"{sign}{pre}{a / 1e6:.2f}M"
    if a >= 1e3:
        return f"{sign}{pre}{a / 1e3:.1f}K"
    if a == int(a):
        return f"{sign}{pre}{int(a):,}"
    return f"{sign}{pre}{a:,.2f}"


def _measure_kpi_card(df: pd.DataFrame, schema, col: str, agg: str, currency: str) -> dict:
    s = pd.to_numeric(df[col], errors="coerce")
    valid = s.dropna()
    n_total = len(df)
    n_valid = len(valid)
    coverage = (n_valid / n_total * 100.0) if n_total else 0.0
    val = an._agg_series(s, agg) if n_valid else None
    agg_prefix = {"sum": "Total", "mean": "Avg", "median": "Median", "count": "Count"}.get(agg, "")
    label = f"{agg_prefix} {col}" if agg != "sum" or an.col_words(col) & {"revenue", "sales", "cost", "profit"} else f"Total {col}"
    if col.lower().startswith(("total ", "avg ", "average ", "median ")):
        label = col
    val_str = f"{int(val):,}" if agg == "count" and val is not None else _format_measure_value(col, val, currency)

    pill = f"{n_valid:,} valid rows"
    pill_class = "pill-purple"
    if schema.date and schema.date in df.columns and n_valid >= 2:
        try:
            tbl, _ = an.period_table(df, schema.date, col, agg)
            comp = tbl[~tbl["partial"] & tbl["value"].notna()]
            if len(comp) >= 2:
                prev_v = float(comp["value"].iloc[-2])
                curr_v = float(comp["value"].iloc[-1])
                if prev_v > 0 and curr_v >= 0:
                    delta = (curr_v - prev_v) / prev_v * 100.0
                    arrow = "↑" if delta >= 0 else "↓"
                    good = (delta <= 0) if an.lower_is_better(col) else (delta >= 0)
                    pill_class = "pill-green" if good else "pill-red"
                    pill = f"{arrow} {delta:+.1f}% vs prior period"
        except Exception:
            pass
    if coverage < 99.5 and "vs prior" not in pill:
        pill = f"{coverage:.0f}% coverage ({n_valid:,} rows)"
        pill_class = "pill-amber" if coverage < 80 else "pill-blue"

    return {"label": label, "value": val_str, "pill": pill, "pill_class": pill_class, "col": col, "agg": agg}


def _distinct_kpi_card(df: pd.DataFrame, col: str, label: Optional[str] = None) -> dict:
    s = df[col].dropna()
    n_unique = int(s.nunique())
    n_total = len(df)
    cov = (len(s) / n_total * 100.0) if n_total else 0.0
    nice_lbl = label or f"Unique {col}"
    pill = f"Across {len(s):,} records" if cov >= 99.5 else f"{cov:.0f}% coverage ({len(s):,} rows)"
    return {"label": nice_lbl, "value": f"{n_unique:,}", "pill": pill, "pill_class": "pill-blue", "col": col, "agg": "nunique"}


def compute_objective_kpis(results, prepared, currency: str = "", is_auto: bool = False, ai_kpis: list = None) -> list:
    """Build KPI cards strictly relevant to active objectives (supports >4 cards & AI-deduced KPIs)."""
    df, schema = prepared.df, prepared.schema
    cards, seen = [], set()

    def _add_kpi_spec(item):
        col = item.get("col")
        if not col or col not in df.columns:
            return
        if item.get("type") == "distinct" or item.get("agg") == "nunique":
            key = ("distinct", col, "nunique")
            if key not in seen:
                seen.add(key)
                cards.append(_distinct_kpi_card(df, col, label=item.get("label")))
        else:
            agg = item.get("agg") if item.get("agg") in ob.AGGS else an.default_agg(col)
            key = ("measure", col, agg)
            if key not in seen:
                seen.add(key)
                cards.append(_measure_kpi_card(df, schema, col, agg, currency))

    if ai_kpis and not is_auto:
        for item in ai_kpis:
            _add_kpi_spec(item)

    if not cards:
        for res in results:
            sp = res.spec
            extracted = ob.extract_requested_kpis(sp.text, prepared) if not is_auto else []
            if extracted:
                for item in extracted:
                    _add_kpi_spec(item)
                continue

            for col in (sp.measure, sp.measure2):
                if not col or col not in df.columns:
                    continue
                agg = sp.agg if (col == sp.measure and sp.agg in ("sum", "mean", "median", "count")) else an.default_agg(col)
                _add_kpi_spec({"type": "measure", "col": col, "agg": agg})

    if is_auto:
        ranked_measures = sorted(
            [m for m in schema.measures if m in df.columns],
            key=lambda c: (schema.columns[c].missing_pct, -float(df[c].abs().sum(skipna=True))),
        )
        for col in ranked_measures:
            if len(cards) >= 4:
                break
            agg = an.default_agg(col)
            if ("measure", col, agg) not in seen:
                seen.add(("measure", col, agg))
                cards.append(_measure_kpi_card(df, schema, col, agg, currency))

    if not cards or (is_auto and len(cards) < 4):
        cards.append({
            "label": "Validated Records",
            "value": f"{len(df):,}",
            "pill": f"{len(schema.dimensions)} grouping columns" if schema.dimensions else "Active scope",
            "pill_class": "pill-amber",
        })
    return cards


def expand_dashboard_results(results, prepared, currency: str = "", is_auto: bool = False, target_charts: int = 4) -> list:
    """Deduplicate identical charts and expand multi-KPI overview prompts into distinct relevant visuals."""
    if not results:
        return results

    deduped, seen_sigs = [], set()
    for r in results:
        sp = r.spec
        sig = (sp.kind, sp.measure, sp.measure2, sp.dimension, sp.agg)
        if sig not in seen_sigs:
            seen_sigs.add(sig)
            deduped.append(r)

    if is_auto:
        return deduped

    # Only expand when the user asked pure 'overview' / multi-KPI summary questions (preserve explicit analytical questions)
    non_overview = [r for r in deduped if r.spec.kind != "overview"]
    if non_overview:
        return deduped

    # Broad overview / multi-KPI summary prompt -> build distinct charts using ONLY the measures user asked for
    df, schema = prepared.df, prepared.schema
    requested_measures = []
    seen_m = set()
    for r in results:
        for item in ob.extract_requested_kpis(r.spec.text, prepared):
            if item["type"] == "measure" and item["col"] in schema.measures:
                key = (item["col"], item["agg"])
                if key not in seen_m:
                    seen_m.add(key)
                    requested_measures.append(key)
    if not requested_measures:
        for r in deduped:
            if r.spec.measure and r.spec.measure in schema.measures:
                key = (r.spec.measure, r.spec.agg)
                if key not in seen_m:
                    seen_m.add(key)
                    requested_measures.append(key)
    if not requested_measures:
        return deduped

    # Rank meaningful grouping dimensions (2..25 unique groups, preferring business attributes like Product/Region/Method)
    dims = [
        d for d in schema.dimensions
        if d in df.columns and 2 <= df[d].nunique(dropna=True) <= 25
    ]
    def _dim_priority(d):
        w = an.col_words(d)
        preferred = 0 if (w & {"product", "category", "region", "method", "channel", "segment", "department", "retailer", "delivery"}) else 1
        return (preferred, abs(df[d].nunique(dropna=True) - 5))
    dims.sort(key=_dim_priority)

    planned_specs = []
    used_sigs = set()
    m0, agg0 = requested_measures[0]

    if schema.date:
        planned_specs.append(ob.ObjectiveSpec(
            id="exp_trend", text=f"{m0} Trajectory Over Time", kind="trend",
            measure=m0, agg=agg0, planner="auto",
        ))
        used_sigs.add(("trend", m0, None))

    dim_idx = 0
    for idx, (m, agg) in enumerate(requested_measures):
        if len(planned_specs) >= target_charts or not dims:
            break
        dim = dims[dim_idx % len(dims)]
        dim_idx += 1
        kind = "composition" if (idx == 1 and df[dim].nunique(dropna=True) <= 6 and agg == "sum") else "compare"
        sig = (kind, m, dim)
        if sig in used_sigs:
            continue
        used_sigs.add(sig)
        lbl = {"sum": "Total", "mean": "Avg", "median": "Median", "count": "Count"}.get(agg, "")
        title = f"{lbl} {m} by {dim}" if not m.lower().startswith(lbl.lower()) else f"{m} by {dim}"
        planned_specs.append(ob.ObjectiveSpec(
            id=f"exp_{len(planned_specs)+1}", text=title, kind=kind,
            measure=m, dimension=dim, agg=agg, top_n=10, planner="auto",
        ))

    # If user only asked 1 measure across multiple dimensions, vary across remaining dimensions
    m_i = 0
    while len(planned_specs) < target_charts and dims and dim_idx < len(dims) * 2:
        dim = dims[dim_idx % len(dims)]
        dim_idx += 1
        m, agg = requested_measures[m_i % len(requested_measures)]
        m_i += 1
        sig = ("compare", m, dim)
        if sig in used_sigs or ("composition", m, dim) in used_sigs:
            continue
        used_sigs.add(sig)
        planned_specs.append(ob.ObjectiveSpec(
            id=f"exp_{len(planned_specs)+1}", text=f"{m} by {dim}", kind="compare",
            measure=m, dimension=dim, agg=agg, top_n=10, planner="auto",
        ))

    if not planned_specs:
        return deduped
    expanded = ob.run_objectives(planned_specs, prepared, currency)
    valid = [r for r in expanded if r.finding.status in ("ok", "caution")]
    return valid if valid else deduped


def render_kpi_grid_html(kpi_cards: list) -> str:
    """Responsive KPI grid supporting 1..N cards cleanly (no squishing when >4)."""
    n = len(kpi_cards)
    cols = 3 if n in (5, 6) else min(4, max(1, n))
    cards_html = "".join(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{_h(c["label"])}</div>'
        f'<div class="kpi-value">{_h(c["value"])}</div>'
        f'<div class="kpi-pill {_h(c.get("pill_class", "pill-blue"))}">{_h(c.get("pill", ""))}</div>'
        f'</div>'
        for c in kpi_cards
    )
    return f'<div class="kpi-row" style="grid-template-columns: repeat({cols}, 1fr);">{cards_html}</div>'


def build_objective_briefing(results, prepared, is_auto: bool = False) -> str:
    answered = [r for r in results if r.finding.status in ("ok", "caution") and r.finding.headline]
    if not answered:
        return f"Loaded {len(prepared.df):,} validated records across {len(prepared.df.columns)} columns. Review missing-data decisions or adjust your objectives in the Studio tab."
    prefix = "Auto-Expert summary across your key columns: " if is_auto else ""
    snippets, seen = [], set()
    for r in answered:
        s = r.finding.headline.rstrip(".")
        if s not in seen:
            seen.add(s)
            snippets.append(s)
        if len(snippets) >= 2:
            break
    return prefix + ". ".join(snippets) + "."


def _clean_chart_title(sp) -> str:
    """Turn long conversational questions into crisp 2-4 word Studio card titles."""
    txt = str(sp.text or "").strip()
    if len(txt) <= 34 and not txt.endswith("?"):
        return txt
    if sp.kind == "trend" and sp.measure:
        return f"{sp.measure} Trajectory"
    if sp.kind == "composition" and sp.dimension:
        return f"{sp.dimension} Distribution"
    if sp.kind == "compare" and sp.dimension and sp.measure:
        w = an.col_words(sp.dimension)
        if w & {"product", "sku", "item"}:
            return f"{sp.dimension} Leaderboard"
        if w & {"category", "vertical", "segment"}:
            return f"{sp.dimension} Portfolio"
        if w & {"region", "area", "zone", "location"}:
            return f"{sp.dimension}al Distribution" if sp.dimension.lower() == "region" else f"{sp.dimension} Breakdown"
        return f"{sp.measure} by {sp.dimension}"
    if sp.kind == "change" and sp.measure:
        return f"{sp.measure} Variance"
    if sp.kind == "distribution" and sp.measure:
        return f"{sp.measure} Spread"
    if sp.kind == "relationship" and sp.measure and sp.measure2:
        return f"{sp.measure} vs {sp.measure2}"
    return txt[:34] + ("…" if len(txt) > 34 else "")


def build_objective_takeaways(results) -> list:
    items = []
    icons = ["📈", "🏆", "📍", "⚡", "📌", "🔍"]
    for i, r in enumerate(results[:3]):
        f = r.finding
        title = _clean_chart_title(r.spec).upper()
        if f.status in ("ok", "caution"):
            body = f.headline
            if f.details:
                body += " " + f.details[0]
            items.append({"icon": icons[i % len(icons)], "title": title, "body": body})
        else:
            items.append({"icon": "⚠️", "title": title, "body": f.headline})
    return items


def render_studio_tab(df: pd.DataFrame, currency: str = "", api_key: str = None, consume_ai_fn=None):
    """Render Tab 3 (Objectives & Data Studio) controls and return live prepared state + results."""
    sig = _sig(df)
    _state_reset_if_new(sig)
    prep = _prepare(df, sig)

    _section_data(prep)
    policies, derive = _section_missing(prep, sig)
    handled = ob.apply_handling(prep, policies, derive)
    hp = handled.prepared
    notes = [n for n in handled.log if n]
    if notes:
        with st.expander(f"What these choices changed ({len(notes)})"):
            for n in notes:
                st.write("• " + n)
    if handled.estimated_cells:
        st.info("Filled values are estimates: " + ", ".join(f"{c} ({n} cells)" for c, n in handled.estimated_cells.items()) + ". Answers using them say so.")

    if len(hp.df) == 0:
        st.error("Your choices removed every row. Pick a gentler option for at least one column.")
        return sig, prep, handled, hp, [], [], False, []

    prev_q_count = len(st.session_state.get("oq_questions", []))
    _section_questions(hp)
    qs = st.session_state["oq_questions"]
    if prev_q_count == 0 and len(qs) > 0:
        st.rerun()

    if qs:
        c_lbl, c_clr = st.columns([4, 1])
        c_lbl.caption(f"{len(qs)} custom objective(s) active — driving your Executive Dashboard & Slide Deck.")
        if c_clr.button("Clear all objectives", key=f"oq_clr_all_{sig}", use_container_width=True):
            st.session_state["oq_questions"] = []
            st.session_state["oq_over"] = {}
            st.session_state["oq_accept"] = set()
            st.session_state.pop("oq_deck", None)
            st.rerun()

    specs, ai_kpis, errors, parent_map = [], [], [], {}
    for q in qs:
        k_items, q_specs, err = _plan_smart(hp, q, sig, api_key=api_key, consume_ai_fn=consume_ai_fn)
        if err:
            errors.append((q, err))
        else:
            ai_kpis.extend(k_items)
            for sp in q_specs:
                specs.append(sp)
                parent_map[sp.id] = q["id"]
    for q, err in errors:
        st.error(f"'{q['text']}': {err}")

    user_results = ob.run_objectives(specs, hp, currency, st.session_state["oq_accept"]) if specs else []
    if user_results:
        st.markdown("#### Active Objectives & Plan Controls")
        for i, res in enumerate(user_results, 1):
            f, sp = res.finding, res.spec
            p_qid = parent_map.get(sp.id, sp.id)
            with st.container(border=True):
                st.markdown(f"**Q{i}. {sp.text}**")
                planner_lbl = "✨ Gemini AI" if sp.planner == "llm" else "Rules"
                st.caption(f"{STATUS_LABEL.get(f.status, f.status)}  ·  {KIND_LABEL.get(sp.kind, sp.kind)}  ·  {planner_lbl}  ·  confidence: {f.confidence}")
                if f.status in ("decision", "blocked") and not res.feasibility.structural:
                    for r_txt in res.feasibility.reasons:
                        st.warning(r_txt)
                    if st.button("Answer anyway, I accept the risk", key=f"oq_acc_tab_{sp.id}"):
                        st.session_state["oq_accept"].add(sp.id)
                        st.session_state.pop("oq_deck", None)
                        st.rerun()
                else:
                    st.write(f.headline)
                with st.expander("Details, caveats & data"):
                    for d in f.details:
                        st.write("• " + d)
                    for c in f.caveats:
                        st.warning(c)
                    if f.table is not None and len(f.table):
                        st.dataframe(f.table.head(100), use_container_width=True, hide_index=True)
                _adjust_widget(hp, sp, sp.id)
                if p_qid == sp.id and st.button("🗑 Remove this question", key=f"oq_rm_tab_{sp.id}"):
                    _remove_question(p_qid)
                    st.rerun()

    return sig, prep, handled, hp, specs, user_results, len(qs) == 0, ai_kpis


def run_auto_expert_objectives(hp, currency: str = "", limit: int = 4) -> list:
    """Select diverse, Studio-balanced expert visuals (1 trend + distinct dimensions) when no goals set."""
    s, df = hp.schema, hp.df
    if not s.measures:
        return []
    ranked_measures = sorted(
        [m for m in s.measures if m in df.columns],
        key=lambda c: (s.columns[c].missing_pct, -float(df[c].abs().sum(skipna=True))),
    )
    m0 = ranked_measures[0]
    dims = [d for d in s.dimensions if d in df.columns and 2 <= df[d].nunique(dropna=True) <= 40]
    dims.sort(key=lambda d: (
        0 if (an.col_words(d) & {"category", "region", "product", "method", "channel", "segment"}) else 1,
        df[d].nunique(dropna=True),
    ))

    specs = []
    if s.date:
        specs.append(ob.ObjectiveSpec(id="auto_trend", text="Performance Trajectory", kind="trend", measure=m0, agg=an.default_agg(m0), planner="auto"))

    for d in dims:
        if len(specs) >= limit:
            break
        nunique = df[d].nunique(dropna=True)
        w = an.col_words(d)
        if w & {"region", "area", "zone"} or (len(specs) >= 2 and nunique <= 6):
            kind = "composition"
            title = "Regional Distribution" if w & {"region"} else f"{d} Distribution"
        elif w & {"product", "sku", "item"} or nunique > 7:
            kind = "compare"
            title = "Product Leaderboard" if w & {"product"} else f"{d} Leaderboard"
        else:
            kind = "compare"
            title = "Category Portfolio" if w & {"category"} else f"{d} Portfolio"
        specs.append(ob.ObjectiveSpec(
            id=f"auto_{len(specs)+1}", text=title, kind=kind,
            measure=m0, dimension=d, agg=an.default_agg(m0), top_n=10, planner="auto",
        ))

    if len(specs) < limit and not dims:
        specs.append(ob.ObjectiveSpec(id="auto_dist", text=f"{m0} Distribution", kind="distribution", measure=m0, agg=an.default_agg(m0), planner="auto"))

    return ob.run_objectives(specs, hp, currency)


def render_objective_dashboard_tab(
    hp,
    results,
    kpi_cards,
    scope_labels,
    sel_scope_idx,
    is_auto: bool,
    currency: str,
    brand_color: str,
    render_clean_btn_fn,
    api_key: str = None,
    report_title: str = "Analysis Report",
    trigger_ai: bool = False,
    consume_ai_fn=None,
):
    """Render Tab 1 (Executive Dashboard) in Linear Obsidian style driven by active objectives."""
    used_llm = any(r.spec.planner == "llm" for r in results)
    if is_auto:
        mode_badge = "✦ Auto-Expert Analysis"
    elif used_llm:
        mode_badge = f"✨ Gemini AI · {len(results)} Visual{'s' if len(results) != 1 else ''}"
    else:
        mode_badge = f"🎯 {len(results)} Active Objective{'s' if len(results) != 1 else ''}"
    hygiene_pill = (
        f'<span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:10px;'
        f'background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.25);color:#34D399;margin-left:8px;">'
        f'✔ {len(hp.df):,} Records Usable</span>'
    )

    col_head, col_scope, col_dl = st.columns([2.6, 1.1, 0.9])
    with col_head:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;padding-top:4px;">'
            f'<span style="font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;'
            f'background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);color:#A5B4FC;">'
            f'{_h(mode_badge)}</span>{hygiene_pill}</div>',
            unsafe_allow_html=True,
        )
    with col_scope:
        if len(scope_labels) > 1:
            st.selectbox(
                "Executive Time Scope",
                scope_labels,
                index=sel_scope_idx,
                key="global_time_scope",
                label_visibility="collapsed",
                help="Filter dashboard KPIs, charts, and slides by time horizon",
            )
    with col_dl:
        render_clean_btn_fn("obj_dash")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    pending_decisions = [r for r in results if r.finding.status in ("decision", "blocked") and not r.feasibility.structural]
    if pending_decisions:
        st.warning(
            f"⚠️ {len(pending_decisions)} question(s) paused due to missing values. "
            f"Open the **🎯 Objectives & Data Studio** tab to fill blanks or accept the risk."
        )

    ai_nar = None
    if api_key and results:
        b_cache = st.session_state.setdefault("oq_ai_briefings", {})
        b_key = (
            len(hp.df), currency,
            tuple((k["label"], k["value"]) for k in kpi_cards),
            tuple((r.spec.id, r.finding.headline) for r in results),
        )
        if trigger_ai and (consume_ai_fn is None or consume_ai_fn()):
            from ai_narrator import generate_objective_briefing
            with st.spinner("🧠 Synthesizing executive briefing with Gemini..."):
                res_nar = generate_objective_briefing(
                    kpi_cards, results, report_title=report_title, api_key=api_key
                )
            if isinstance(res_nar, dict) and res_nar.get("executive_summary"):
                b_cache[b_key] = res_nar
                st.toast("✨ Gemini executive briefing & takeaways generated!", icon="🧠")
        ai_nar = b_cache.get(b_key)

    briefing = (ai_nar or {}).get("executive_summary") or build_objective_briefing(results, hp, is_auto=is_auto)
    brief_tag = "✨ AI EXECUTIVE BRIEFING:" if (ai_nar and ai_nar.get("executive_summary")) else "✦ EXECUTIVE BRIEFING:"
    st.markdown(
        f'<div style="background:linear-gradient(135deg, rgba(99,102,241,0.08), rgba(56,189,248,0.04));'
        f'border:1px solid rgba(99,102,241,0.22);border-radius:8px;padding:12px 18px;margin-bottom:18px;'
        f'font-size:13px;color:#E2E8F0;line-height:1.6;">'
        f'<span style="font-weight:700;color:#A5B4FC;margin-right:6px;">{brief_tag}</span>'
        f'{_h(briefing)}</div>',
        unsafe_allow_html=True,
    )

    if kpi_cards:
        st.markdown(render_kpi_grid_html(kpi_cards), unsafe_allow_html=True)

    if not results:
        st.info("No numeric measures detected to plot. Check column roles in the **🎯 Objectives & Data Studio** tab.")
        return

    # Clean 2-Column Studio Chart Grid matching Image 2 (dark #111827 charts, compact controls, zero card clutter)
    sig_prefix = hashlib.md5(f"{len(hp.df)}_{currency}".encode()).hexdigest()[:6]
    all_measures = list(hp.schema.measures)
    valid_dims = [d for d in hp.schema.dimensions if d in hp.df.columns and 2 <= hp.df[d].nunique(dropna=True) <= 40]
    grain_map = {"Monthly": "M", "Quarterly": "Q", "Weekly": "W", "Daily": "D"}

    for row_start in range(0, len(results), 2):
        row_items = results[row_start : row_start + 2]
        cols = st.columns(2)
        for col_idx, res in enumerate(row_items):
            f, sp = res.finding, res.spec
            eff_dim = sp.dimension or (f.chart or {}).get("x")
            q_hash = hashlib.md5(f"{sp.kind}_{sp.measure}_{eff_dim}_{sp.text}".encode()).hexdigest()[:6]
            card_key = f"{sp.id}_{q_hash}_{row_start}_{col_idx}_{sig_prefix}"
            with cols[col_idx]:
                card_title = _clean_chart_title(sp)
                if f.status in ("decision", "blocked", "error"):
                    st.markdown(f'<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">{_h(card_title)}</div>', unsafe_allow_html=True)
                    st.warning(f.headline)
                    continue

                base_type = (f.chart or {}).get("type", "")
                chosen_style = None
                chosen_top_n = None
                active_finding = f

                if base_type == "line" and hp.schema.date and sp.measure in hp.df.columns:
                    c_h, c_gr, c_st = st.columns([1.8, 1.3, 1.3])
                    c_h.markdown(f'<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">{_h(card_title)}</div>', unsafe_allow_html=True)
                    sel_gr = c_gr.selectbox("Granularity", ["Monthly", "Quarterly", "Weekly", "Daily"], key=f"obj_gr_{card_key}", label_visibility="collapsed")
                    chosen_style = c_st.selectbox("Style", ["Grouped Bars", "Line & Area", "Growth %"], key=f"obj_st_{card_key}", label_visibility="collapsed")
                    try:
                        tbl, _ = an.period_table(hp.df, hp.schema.date, sp.measure, sp.agg, grain=grain_map[sel_gr])
                        used = tbl[tbl["n"] > 0].copy()
                        if not used.empty:
                            y_lbl = f"{sp.agg.title()} {sp.measure}"
                            active_finding = an.Finding(
                                objective_id=f.objective_id, kind=f.kind, question=f.question,
                                status=f.status, headline=f.headline, details=f.details,
                                table=used.rename(columns={"label": "Period", "value": y_lbl}),
                                chart={"type": "line", "x": "Period", "y": y_lbl},
                                caveats=f.caveats, assumptions=f.assumptions,
                                coverage_pct=f.coverage_pct, n_rows=f.n_rows, confidence=f.confidence,
                            )
                    except Exception:
                        pass

                elif base_type == "bar" and sp.kind == "change" and eff_dim and all_measures and valid_dims:
                    c_h, c_m, c_d, c_st = st.columns([1.5, 1.05, 1.05, 1.0])
                    m_idx = all_measures.index(sp.measure) if sp.measure in all_measures else 0
                    d_idx = valid_dims.index(eff_dim) if eff_dim in valid_dims else 0
                    sel_m = c_m.selectbox("Metric", all_measures, index=m_idx, key=f"obj_met_{card_key}", label_visibility="collapsed")
                    sel_d = c_d.selectbox("Dimension", valid_dims, index=d_idx, key=f"obj_dim_{card_key}", label_visibility="collapsed")
                    if sel_m != sp.measure or sel_d != eff_dim:
                        try:
                            new_agg = sp.agg if (sel_m == sp.measure and sp.agg in ob.AGGS) else an.default_agg(sel_m)
                            new_sp = ob.ObjectiveSpec(
                                id=sp.id, text=f"{sel_m} Variance by {sel_d}", kind="change",
                                measure=sel_m, dimension=sel_d, agg=new_agg,
                                base_range=sp.base_range, focus_range=sp.focus_range,
                                base_label=sp.base_label, focus_label=sp.focus_label,
                                assumptions=list(sp.assumptions),
                            )
                            active_finding = ob.ANALYSES["change"](hp.df, hp.schema, new_sp, currency)
                            card_title = f"{sel_m} Variance"
                        except Exception:
                            pass
                    # Keep diverging (+ / -) variance charts honest: Donut/Pie only when values don't cross zero
                    cy = (active_finding.chart or {}).get("y")
                    vals = pd.to_numeric(active_finding.table[cy], errors="coerce").dropna() if (active_finding.table is not None and cy in active_finding.table.columns) else pd.Series(dtype=float)
                    has_neg = vals.empty or bool((vals < 0).any()) or float(vals.sum()) <= 0
                    style_opts = ["Vertical Bar", "Horizontal Bar"] if has_neg else ["Vertical Bar", "Horizontal Bar", "Donut", "Pie"]
                    st_key = f"obj_st_{card_key}"
                    if st.session_state.get(st_key) not in style_opts:
                        st.session_state[st_key] = style_opts[0]
                    chosen_style = c_st.selectbox("Style", style_opts, key=st_key, label_visibility="collapsed")
                    c_h.markdown(f'<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">{_h(card_title)}</div>', unsafe_allow_html=True)

                elif base_type == "bar" and eff_dim and len(all_measures) >= 1:
                    c_h, c_m, c_st, c_n = st.columns([1.6, 1.15, 1.15, 0.7])
                    m_idx = all_measures.index(sp.measure) if sp.measure in all_measures else 0
                    sel_m = c_m.selectbox("Metric", all_measures, index=m_idx, key=f"obj_met_{card_key}", label_visibility="collapsed")
                    if sel_m != sp.measure:
                        try:
                            new_agg = an.default_agg(sel_m)
                            new_sp = ob.ObjectiveSpec(
                                id=sp.id, text=f"{sel_m} by {eff_dim}",
                                kind=sp.kind if sp.kind in ("compare", "composition") else "compare",
                                measure=sel_m, dimension=eff_dim, agg=new_agg, top_n=12,
                                direction=sp.direction,
                            )
                            active_finding = ob.ANALYSES[new_sp.kind](hp.df, hp.schema, new_sp, currency)
                        except Exception:
                            pass
                    n_groups = len(active_finding.table) if active_finding.table is not None else 0
                    cy = (active_finding.chart or {}).get("y")
                    vals = pd.to_numeric(active_finding.table[cy], errors="coerce").dropna() if (active_finding.table is not None and cy in active_finding.table.columns) else pd.Series(dtype=float)
                    has_neg = vals.empty or bool((vals < 0).any()) or float(vals.sum()) <= 0
                    if has_neg:
                        default_styles = ["Vertical Bar", "Horizontal Bar"]
                    elif sp.kind == "composition" or (n_groups <= 6 and "Region" in str(eff_dim)):
                        default_styles = ["Donut", "Vertical Bar", "Horizontal Bar", "Pie"]
                    elif n_groups <= 6 and any(w in str(eff_dim).lower() for w in ("category", "method", "channel", "segment")):
                        default_styles = ["Horizontal Bar", "Donut", "Vertical Bar", "Pie"]
                    else:
                        default_styles = ["Vertical Bar", "Horizontal Bar", "Donut", "Pie"]
                    st_key = f"obj_st_{card_key}"
                    if st.session_state.get(st_key) not in default_styles:
                        st.session_state[st_key] = default_styles[0]
                    chosen_style = c_st.selectbox("Style", default_styles, key=st_key, label_visibility="collapsed")
                    sel_top = c_n.selectbox("Top", [5, 10, "All"], index=0 if n_groups > 6 else 1, key=f"obj_top_{card_key}", label_visibility="collapsed")
                    chosen_top_n = None if sel_top == "All" else int(sel_top)
                    c_h.markdown(f'<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">{_h(card_title)}</div>', unsafe_allow_html=True)

                else:
                    st.markdown(f'<div style="font-size:14px;font-weight:700;color:#F8FAFC;padding:6px 0;">{_h(card_title)}</div>', unsafe_allow_html=True)

                if active_finding.status in ("blocked", "error") or active_finding.table is None or active_finding.table.empty:
                    st.warning(active_finding.headline or "Not enough valid rows for this selection.")
                    continue

                fig = figure_for(
                    active_finding,
                    dark=True,
                    brand_color=brand_color,
                    chart_style=chosen_style,
                    currency=currency,
                    top_n=chosen_top_n,
                )
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True, key=f"oq_dash_fig_{card_key}")
                elif active_finding.details:
                    for d in active_finding.details[:4]:
                        st.write("• " + d)

    takeaways = (ai_nar or {}).get("takeaways") or build_objective_takeaways(results)
    if takeaways:
        ai_badge = '<span style="margin-left:10px;font-size:11px;font-weight:600;padding:2px 8px;border-radius:10px;background:rgba(99,102,241,0.2);border:1px solid #6366F1;color:#A5B4FC;">✦ AI-Synthesized</span>' if (ai_nar and ai_nar.get("takeaways")) else ""
        st.markdown(f'<div class="section-title">Automated Executive Takeaways{ai_badge}</div>', unsafe_allow_html=True)
        cards_html = "".join(
            f'<div class="insight-card"><div class="insight-title">{_h(t["icon"])} {_h(t["title"])}</div>'
            f'<div class="insight-body">{_h(t["body"])}</div></div>'
            for t in takeaways
        )
        st.markdown(f'<div class="insight-grid">{cards_html}</div>', unsafe_allow_html=True)


def build_objective_slide_previews(results, kpi_cards, prepared, title, mode_label, brand_color, logo_b64=None) -> list:
    """Build 16:9 dark Linear Obsidian slide preview dicts aligned with objective_deck.py."""
    accent = brand_color if re.fullmatch(r"#[0-9A-Fa-f]{6}", str(brand_color or "")) else "#6366F1"
    logo_tag = f'<img src="{logo_b64}" style="max-height:42px;max-width:140px;object-fit:contain;margin-bottom:14px;display:block;" />' if logo_b64 else ""
    n_ok = sum(1 for r in results if r.finding.status in ("ok", "caution"))

    slides = [{
        "num": "01",
        "name": "Executive Cover",
        "icon": "🏷️",
        "tag": f"EXECUTIVE BRIEFING · {_h(mode_label.upper())}",
        "html": (
            f'<div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:20px 0;">{logo_tag}'
            f'<h1 style="font-size:36px;font-weight:800;color:#F8FAFC;margin:0 0 12px 0;letter-spacing:-0.02em;line-height:1.2;">{_h(title)}</h1>'
            f'<p style="font-size:15px;color:#94A3B8;margin:0 0 24px 0;line-height:1.6;">{n_ok} of {len(results)} Objective Analyses Answered</p>'
            f'<div style="display:flex;gap:20px;font-size:12px;color:#64748B;">'
            f'<span style="color:{accent};">● Validated Schema</span><span>{len(prepared.df):,} Records</span><span>Confidential · Boardroom Ready</span></div></div>'
        ),
        "notes": f"Welcome everyone. Today we are reviewing {title}, covering {n_ok} objective-driven analyses across {len(prepared.df):,} validated records.",
    }]

    if kpi_cards:
        cols = 3 if len(kpi_cards) in (5, 6) else min(4, max(1, len(kpi_cards)))
        k_html = "".join(
            f'<div style="background:#111827;border:1px solid #1F2937;border-radius:10px;padding:14px;">'
            f'<div style="font-size:10px;color:#64748B;font-weight:700;letter-spacing:0.06em;">{_h(k["label"].upper())}</div>'
            f'<div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-top:6px;">{_h(k["value"])}</div>'
            f'<div style="font-size:10.5px;color:#38BDF8;margin-top:4px;">{_h(k.get("pill", ""))}</div></div>'
            for k in kpi_cards[:8]
        )
        slides.append({
            "num": "02",
            "name": "KPI Matrix",
            "icon": "📌",
            "tag": "EXECUTIVE HIGHLIGHTS · SLIDE 02",
            "html": (
                f'<div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:10px 0;">'
                f'<div style="font-size:22px;font-weight:800;color:#F8FAFC;margin-bottom:16px;">Key Performance Indicators</div>'
                f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:12px;">{k_html}</div></div>'
            ),
            "notes": "Here are the core KPIs tied directly to our active objectives, computed strictly on validated non-blank records.",
        })

    for idx, res in enumerate(results, 1):
        f, sp = res.finding, res.spec
        s_num = f"{len(slides) + 1:02d}"
        bullets = "".join(f'<li style="margin-bottom:6px;">{_h(d)}</li>' for d in f.details[:4])
        cav = "".join(f'<div style="font-size:11.5px;color:#FBBF24;margin-top:4px;">⚠ {_h(c)}</div>' for c in f.caveats[:2])
        slides.append({
            "num": s_num,
            "name": f"Q{idx}",
            "icon": "📊",
            "tag": f"QUESTION {idx} · {_h(KIND_LABEL.get(sp.kind, sp.kind).upper())}",
            "html": (
                f'<div style="flex:1;display:flex;flex-direction:column;justify-content:space-between;padding:10px 0;">'
                f'<div><div style="font-size:18px;font-weight:800;color:#F8FAFC;margin-bottom:8px;">{_h(sp.text)}</div>'
                f'<div style="font-size:14px;color:{accent};font-weight:600;margin-bottom:14px;">{_h(f.headline)}</div>'
                f'<ul style="font-size:13px;color:#CBD5E1;padding-left:18px;margin:0;">{bullets}</ul>{cav}</div>'
                f'<div style="font-size:11px;color:#64748B;">Confidence: {_h(f.confidence)} · {f.n_rows:,} rows · {f.coverage_pct:.0f}% coverage</div></div>'
            ),
            "notes": f.headline + (" " + "; ".join(f.assumptions) if f.assumptions else ""),
        })

    prep_bullets = "".join(f'<li style="margin-bottom:4px;">{_h(l)}</li>' for l in (prepared.log or ["No cleaning changes were needed."])[:5])
    slides.append({
        "num": f"{len(slides) + 1:02d}",
        "name": "Data Notes",
        "icon": "🛡️",
        "tag": "METHODOLOGY & ASSUMPTIONS",
        "html": (
            f'<div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:10px 0;">'
            f'<div style="font-size:20px;font-weight:800;color:#F8FAFC;margin-bottom:12px;">How This Analysis Was Done</div>'
            f'<ul style="font-size:12.5px;color:#CBD5E1;padding-left:18px;margin:0;">{prep_bullets}</ul></div>'
        ),
        "notes": "Summary of automated data preparation, schema role detection, and deterministic calculation assumptions.",
    })
    return slides

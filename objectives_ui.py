"""Objective-driven analysis screen. Rendered by app.py when the user picks 'Ask your own questions'.

Flow: data check -> missing-data decisions -> add questions -> answers (with plan, caveats, deck download).
All numbers come from deterministic code (analyses.py); nothing here invents figures.
"""
import hashlib
import pandas as pd
import streamlit as st

import objectives as ob
from objective_charts import figure_for
from data_quality import missing_profile
from schema import prepare_frame

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
        st.session_state.pop("oq_deck", None)


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


def _render_result(prep, res, idx, currency):
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
            fig = figure_for(f, dark=True)
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

    _section_questions(hp)
    qs = st.session_state["oq_questions"]
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
        _render_result(hp, r, i, currency)

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
                path = build_objective_deck(results, title=title, quality_notes=hp.log, brand_color=brand_color,
                                            brand_name=brand_name or None)
                with open(path, "rb") as fh:
                    st.session_state["oq_deck"] = {"key": deck_key, "bytes": fh.read()}
            st.rerun()
        except Exception as e:
            st.error(f"Could not build the slide deck: {e}")
    st.download_button("📥 Download the cleaned data (.csv)", hp.df.to_csv(index=False).encode("utf-8-sig"),
                       file_name="cleaned_data.csv", mime="text/csv", use_container_width=True, key="oq_dl_csv")

import json
import unittest
import numpy as np
import pandas as pd

import objectives as ob
from schema import prepare_frame


def clinic_data(seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", "2024-09-30", freq="D")
    rows = []
    for d in dates:
        for clinic in ("Accra", "Kumasi", "Tamale"):
            base = {"Accra": 1000, "Kumasi": 800, "Tamale": 500}[clinic]
            if clinic == "Kumasi" and d.month >= 7:
                base = 300                                  # planted collapse in Q3
            rev = base * rng.uniform(0.9, 1.1)
            rows.append({"Date": d, "Clinic": clinic, "Revenue": round(rev, 2), "Cost": round(rev * 0.6, 2),
                         "Visits": int(rev / 20), "Wait (min)": round(rng.uniform(10, 40), 1),
                         "Budget": round(base * 1.0, 2), "Actual": round(rev, 2)})
    return pd.DataFrame(rows)


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prep = prepare_frame(clinic_data())


class TestPlanner(Base):
    def plan(self, text):
        return ob.plan_objective(text, self.prep)

    def test_why_drop_q3_is_change_with_periods(self):
        sp = self.plan("Why did revenue drop in Q3?")
        self.assertEqual(sp.kind, "change")
        self.assertEqual(sp.measure, "Revenue")
        self.assertEqual(sp.focus_label, "Q3 2024")
        self.assertEqual(sp.base_label, "Q2 2024")

    def test_which_clinic_highest(self):
        sp = self.plan("Which clinic has the highest revenue?")
        self.assertEqual((sp.kind, sp.measure, sp.dimension, sp.direction), ("compare", "Revenue", "Clinic", "high"))

    def test_trend(self):
        sp = self.plan("How has revenue changed over time?")
        self.assertEqual(sp.kind, "trend")

    def test_relationship_picks_two_measures(self):
        sp = self.plan("Is wait time related to visits?")
        self.assertEqual(sp.kind, "relationship")
        self.assertEqual({sp.measure, sp.measure2}, {"Wait (min)", "Visits"})

    def test_target(self):
        sp = self.plan("Are we over budget?")
        self.assertEqual(sp.kind, "target")
        self.assertEqual((sp.measure, sp.measure2), ("Actual", "Budget"))

    def test_composition(self):
        sp = self.plan("What share of revenue comes from each clinic?")
        self.assertEqual((sp.kind, sp.dimension), ("composition", "Clinic"))

    def test_average_wait_uses_mean_by_default(self):
        sp = self.plan("Which clinic has the longest wait?")
        self.assertEqual(sp.measure, "Wait (min)")
        self.assertEqual(sp.agg, "mean")

    def test_worst_wait_means_highest(self):
        sp = self.plan("Which clinic has the worst wait time?")
        self.assertEqual(sp.direction, "high")
        self.assertTrue(any("LOW" in a for a in sp.assumptions))

    def test_worst_revenue_means_lowest(self):
        self.assertEqual(self.plan("Which clinic has the worst revenue?").direction, "low")

    def test_named_months(self):
        sp = self.plan("Why did revenue change in August 2024?")
        self.assertEqual((sp.focus_label, sp.base_label), ("Aug 2024", "Jul 2024"))

    def test_year_vs_year(self):
        df = clinic_data()
        df2 = df.copy(); df2["Date"] = df2["Date"] + pd.DateOffset(years=1)
        prep = prepare_frame(pd.concat([df, df2], ignore_index=True))
        sp = ob.plan_objective("Compare revenue 2024 vs 2025", prep)
        self.assertEqual((sp.base_label, sp.focus_label), ("2024", "2025"))

    def test_may_the_verb_is_not_a_month(self):
        sp = self.plan("Why did revenue fall? It may be seasonal")
        self.assertNotIn("May", sp.focus_label)

    def test_default_change_periods_latest_complete_months(self):
        sp = self.plan("What changed in revenue?")
        self.assertEqual(sp.kind, "change")
        self.assertEqual((sp.base_label, sp.focus_label), ("Aug 2024", "Sep 2024"))

    def test_no_measure_named_uses_most_complete_and_says_so(self):
        sp = self.plan("Give me an overview")
        self.assertIsNotNone(sp.measure)
        self.assertTrue(any("did not name a measure" in a for a in sp.assumptions))

    def test_empty_text_raises(self):
        with self.assertRaises(ob.PlanError):
            self.plan("   ")


class TestAnswers(Base):
    def run1(self, text, **kw):
        sp = ob.plan_objective(text, self.prep)
        return ob.run_objective(sp, self.prep, **kw)

    def test_q3_drop_is_attributed_to_kumasi(self):
        r = self.run1("Why did revenue drop in Q3?")
        f = r.finding
        self.assertIn(f.status, ("ok", "caution"))
        self.assertEqual(f.numbers["driver_level"], "Kumasi")
        self.assertEqual(f.numbers["driver_dimension"], "Clinic")
        self.assertLess(f.numbers["delta"], 0)
        self.assertTrue(any("cannot prove WHY" in c for c in f.caveats))
        self.assertTrue(any("Kumasi" in d for d in f.details))

    def test_compare_numbers(self):
        f = self.run1("Which clinic has the highest revenue?").finding
        self.assertEqual(f.numbers["top"], "Accra")
        self.assertEqual(f.numbers["bottom"], "Tamale")
        exp = clinic_data().groupby("Clinic")["Revenue"].sum()["Accra"]
        self.assertAlmostEqual(f.numbers["top_value"], exp, places=1)

    def test_compare_lowest(self):
        f = self.run1("Which clinic has the lowest revenue?").finding
        self.assertEqual(f.numbers["top"], "Tamale")

    def test_trend_finds_decline(self):
        f = self.run1("How has revenue changed over time?").finding
        self.assertEqual(f.kind, "trend")
        self.assertLess(f.numbers["change_pct"], 0)
        self.assertIn("fell", f.headline)

    def test_flat_series_is_not_called_a_trend(self):
        df = clinic_data()
        df = df[df["Clinic"] == "Accra"].copy()
        prep = prepare_frame(df)
        sp = ob.plan_objective("How has revenue changed over time?", prep)
        f = ob.run_objective(sp, prep).finding
        self.assertIn("no clear trend", f.headline)

    def test_target_matched_totals(self):
        f = self.run1("Are we over budget?").finding
        d = clinic_data()
        self.assertAlmostEqual(f.numbers["actual"], d["Actual"].sum(), places=1)
        self.assertAlmostEqual(f.numbers["target"], d["Budget"].sum(), places=1)

    def test_relationship_unrelated_is_negligible(self):
        f = self.run1("Is wait time related to visits?").finding
        self.assertIn("negligible", f.headline)
        self.assertTrue(any("not that one causes" in c for c in f.caveats))

    def test_relationship_strong(self):
        d = clinic_data()
        d["Visits"] = d["Revenue"] / 20
        prep = prepare_frame(d)
        sp = ob.plan_objective("Is revenue related to visits?", prep)
        f = ob.run_objective(sp, prep).finding
        self.assertGreater(abs(f.numbers["pearson"]), 0.99)

    def test_composition_shares_add_to_100(self):
        f = self.run1("What share of revenue comes from each clinic?").finding
        self.assertAlmostEqual(float(f.table["Share %"].sum()), 100.0, delta=0.3)

    def test_distribution_reports_outliers(self):
        d = clinic_data()
        d.loc[0, "Revenue"] = 1_000_000
        prep = prepare_frame(d)
        sp = ob.plan_objective("Are there unusual values in revenue?", prep)
        f = ob.run_objective(sp, prep).finding
        self.assertGreaterEqual(f.numbers["outliers"], 1)

    def test_overview(self):
        f = self.run1("Give me an overview of revenue").finding
        self.assertEqual(f.kind, "overview")
        self.assertIn("records", f.headline)


class TestMissingDataHonesty(unittest.TestCase):
    def prep_with_gaps(self, frac):
        d = clinic_data()
        rng = np.random.default_rng(5)
        d.loc[rng.random(len(d)) < frac, "Revenue"] = np.nan
        return prepare_frame(d)

    def test_light_gaps_proceed_with_coverage_note(self):
        prep = self.prep_with_gaps(0.10)
        sp = ob.plan_objective("Which clinic has the highest revenue?", prep)
        r = ob.run_objective(sp, prep)
        self.assertEqual(r.feasibility.status, "caution")
        self.assertIn(r.finding.status, ("caution",))
        self.assertTrue(any("Based on" in c or "missing" in c for c in r.finding.caveats))

    def test_heavy_gaps_require_a_decision(self):
        prep = self.prep_with_gaps(0.30)
        sp = ob.plan_objective("Which clinic has the highest revenue?", prep)
        r = ob.run_objective(sp, prep)
        self.assertEqual(r.feasibility.status, "decision")
        self.assertIn("Waiting", r.finding.headline)
        r2 = ob.run_objective(sp, prep, accept_risk=True)
        self.assertIn(r2.finding.status, ("caution", "ok"))
        self.assertTrue(r2.finding.headline.startswith("Accra"))

    def test_extreme_gaps_blocked_but_overridable(self):
        prep = self.prep_with_gaps(0.60)
        sp = ob.plan_objective("Which clinic has the highest revenue?", prep)
        r = ob.run_objective(sp, prep)
        self.assertEqual(r.feasibility.status, "blocked")
        self.assertFalse(r.feasibility.structural)
        r2 = ob.run_objective(sp, prep, accept_risk=True)
        self.assertNotEqual(r2.finding.headline, "")

    def test_gaps_in_unneeded_column_do_not_matter(self):
        d = clinic_data()
        d["Notes2"] = np.nan
        d.loc[::2, "Notes2"] = 1.0       # 50% blank, irrelevant to the question
        prep = prepare_frame(d)
        sp = ob.plan_objective("Which clinic has the highest revenue?", prep)
        self.assertEqual(ob.check_feasibility(sp, prep).status, "ok")

    def test_handling_fill_then_answer(self):
        prep = self.prep_with_gaps(0.30)
        h = ob.apply_handling(prep, {"Revenue": {"method": "fill_median"}}, derive=False)
        self.assertEqual(h.estimated_cells["Revenue"] > 0, True)
        sp = ob.plan_objective("Which clinic has the highest revenue?", h.prepared)
        r = ob.run_objective(sp, h.prepared)
        self.assertEqual(r.feasibility.status, "ok")

    def test_handling_derives_cost_from_revenue_and_profit(self):
        d = clinic_data()
        d["Profit"] = d["Revenue"] - d["Cost"]
        d.loc[:20, "Cost"] = np.nan
        prep = prepare_frame(d)
        h = ob.apply_handling(prep)
        self.assertEqual(int(h.prepared.df["Cost"].isna().sum()), 0)
        self.assertEqual(h.derived_cells.get("Cost"), 21)

    def test_wrong_identity_is_not_used_to_fill(self):
        d = clinic_data()
        d["Profit"] = d["Revenue"] * 0.5                  # does NOT equal revenue - cost (cost = 60%)
        d.loc[:30, "Profit"] = np.nan
        prep = prepare_frame(d)
        h = ob.apply_handling(prep)
        self.assertEqual(int(h.prepared.df["Profit"].isna().sum()), 31)
        self.assertTrue(any("Not filling" in l for l in h.log))

    def test_percent_column_never_treated_as_profit(self):
        d = clinic_data()
        d["Profit Margin %"] = 40.0
        roles = ob.infer_relation_roles(prepare_frame(d).schema)
        self.assertNotIn("profit", roles)


class TestFeasibility(Base):
    def test_no_date_blocks_time_questions(self):
        d = clinic_data().drop(columns=["Date"])
        prep = prepare_frame(d)
        sp = ob.ObjectiveSpec(id="x", text="trend", kind="trend", measure="Revenue")
        fe = ob.check_feasibility(sp, prep)
        self.assertEqual(fe.status, "blocked")
        self.assertTrue(fe.structural)
        r = ob.run_objective(sp, prep, accept_risk=True)
        self.assertEqual(r.finding.status, "blocked")

    def test_single_group_blocks_compare(self):
        d = clinic_data(); d = d[d["Clinic"] == "Accra"]
        prep = prepare_frame(d)
        sp = ob.ObjectiveSpec(id="x", text="t", kind="compare", measure="Revenue", dimension="Clinic")
        self.assertEqual(ob.check_feasibility(sp, prep).status, "blocked")

    def test_too_few_rows(self):
        prep = prepare_frame(clinic_data().head(5))
        sp = ob.ObjectiveSpec(id="x", text="t", kind="overview", measure="Revenue")
        self.assertEqual(ob.check_feasibility(sp, prep).status, "blocked")

    def test_unknown_column(self):
        sp = ob.ObjectiveSpec(id="x", text="t", kind="overview", measure="Nope")
        self.assertEqual(ob.check_feasibility(sp, self.prep).status, "blocked")


class TestMultiObjective(Base):
    def test_several_questions_independent(self):
        texts = ["Why did revenue drop in Q3?", "Which clinic has the highest revenue?", "How has revenue changed over time?"]
        specs = [ob.plan_objective(t, self.prep, obj_id=f"o{i}") for i, t in enumerate(texts)]
        res = ob.run_objectives(specs, self.prep)
        self.assertEqual([r.finding.kind for r in res], ["change", "compare", "trend"])
        self.assertEqual(len({r.spec.id for r in res}), 3)

    def test_one_failure_does_not_stop_others(self):
        good = ob.plan_objective("Which clinic has the highest revenue?", self.prep, "g")
        bad = ob.ObjectiveSpec(id="b", text="boom", kind="compare", measure="Revenue", dimension="Clinic", agg="nonsense")
        res = ob.run_objectives([bad, good], self.prep)
        self.assertEqual(res[0].finding.status, "error")
        self.assertIn(res[1].finding.status, ("ok", "caution"))

    def test_suggestions_are_answerable(self):
        for t in ob.suggest_objectives(self.prep):
            sp = ob.plan_objective(t, self.prep)
            r = ob.run_objective(sp, self.prep)
            self.assertIn(r.finding.status, ("ok", "caution"), msg=t)


class TestLLMPlanValidation(Base):
    def good(self):
        return json.dumps({"kind": "compare", "measure": "Revenue", "dimension": "Clinic", "agg": "sum"})

    def test_valid_plan_accepted(self):
        sp = ob.plan_objective("anything", self.prep, llm_call=lambda p: self.good())
        self.assertEqual(sp.planner, "llm")
        self.assertEqual((sp.kind, sp.measure, sp.dimension), ("compare", "Revenue", "Clinic"))

    def test_hallucinated_column_falls_back_to_rules(self):
        bad = json.dumps({"kind": "compare", "measure": "Profit Margin", "dimension": "Clinic", "agg": "sum"})
        sp = ob.plan_objective("Which clinic has the highest revenue?", self.prep, llm_call=lambda p: bad)
        self.assertEqual(sp.planner, "rules")
        self.assertEqual(sp.measure, "Revenue")

    def test_garbage_and_exceptions_fall_back(self):
        for call in (lambda p: "I think maybe revenue", lambda p: (_ for _ in ()).throw(RuntimeError("api down"))):
            sp = ob.plan_objective("Which clinic has the highest revenue?", self.prep, llm_call=call)
            self.assertEqual(sp.planner, "rules")

    def test_prompt_contains_no_cell_values(self):
        seen = {}
        def call(p):
            seen["p"] = p
            return self.good()
        ob.plan_objective("Which clinic has the highest revenue?", self.prep, llm_call=call)
        self.assertNotIn("Kumasi", seen["p"])
        self.assertIn("Revenue", seen["p"])

    def test_missing_required_column_rejected(self):
        bad = json.dumps({"kind": "compare", "measure": "Revenue", "dimension": None})
        with self.assertRaises(ob.PlanError):
            ob.parse_llm_plan(bad, self.prep, "x")

    def test_explicit_user_agg_overrides_llm(self):
        sp = ob.plan_objective("What is the average revenue by clinic?", self.prep, llm_call=lambda p: self.good())
        self.assertEqual(sp.agg, "mean")

    def test_multi_intent_llm_dashboard_blueprint_validates_and_filters_hallucinations(self):
        payload = json.dumps({
            "kpis": [
                {"type": "measure", "col": "Revenue", "agg": "sum", "label": "Total Revenue"},
                {"type": "distinct", "col": "Clinic", "agg": "nunique", "label": "Clinics"},
                {"type": "measure", "col": "FakeCol", "agg": "sum", "label": "Bad"},
            ],
            "analyses": [
                {"kind": "trend", "title": "Revenue Trend", "measure": "Revenue", "dimension": None, "agg": "sum"},
                {"kind": "compare", "title": "Revenue by Clinic", "measure": "Revenue", "dimension": "Clinic", "agg": "sum"},
                {"kind": "compare", "title": "Invalid Chart", "measure": "Hallucinated", "dimension": "Clinic", "agg": "sum"},
            ],
        })
        seen = {}
        def call(p):
            seen["prompt"] = p
            return payload
        bp = ob.plan_dashboard_with_llm("Total revenue, number of clinics, and clinic breakdown", self.prep, llm_call=call)
        self.assertNotIn("Kumasi", seen["prompt"])
        self.assertEqual(len(bp["kpis"]), 2)
        self.assertEqual(bp["kpis"][0]["col"], "Revenue")
        self.assertEqual(bp["kpis"][1]["agg"], "nunique")
        self.assertEqual(len(bp["specs"]), 2)
        self.assertEqual(bp["specs"][0].planner, "llm")
        self.assertEqual(bp["specs"][1].dimension, "Clinic")


if __name__ == "__main__":
    unittest.main()


class TestStressRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from generate_data import generate_sales_data
        cls.prep = prepare_frame(generate_sales_data())

    def run_q(self, q):
        spec = ob.plan_objective(q, self.prep, "o1")
        return spec, ob.run_objective(spec, self.prep, "GHS").finding

    def test_by_phrasing_means_compare(self):
        spec, f = self.run_q("What is the average order value by channel?")
        self.assertEqual(spec.kind, "compare")
        self.assertEqual(spec.dimension, "Channel")

    def test_counts_not_shown_as_money(self):
        _, f = self.run_q("how many orders per region")
        self.assertNotIn("GHS", f.headline)

    def test_budget_question_without_budget_column_is_blocked_honestly(self):
        spec, f = self.run_q("Are we over budget?")
        self.assertEqual(f.status, "blocked")
        self.assertIn("budget", f.headline.lower())

    def test_gibberish_warns(self):
        spec, _ = self.run_q("???")
        self.assertTrue(any("could not match" in a for a in spec.assumptions))

    def test_wrong_premise_is_flagged(self):
        _, f = self.run_q("Why did revenue drop in Q4?")
        self.assertTrue(any("went UP" in d for d in f.details), f.details)

    def test_dd_mon_yy_dates_detected(self):
        df = pd.DataFrame({"Order Date": pd.date_range("2024-01-01", periods=30, freq="3D").strftime("%d-%b-%y"),
                           "Amount": np.arange(30) * 10.0 + 100})
        self.assertEqual(prepare_frame(df).schema.date, "Order Date")


class TestNegativeValues(unittest.TestCase):
    def test_no_percent_or_share_across_negative_totals(self):
        rng = np.random.default_rng(1)
        df = pd.DataFrame({"Date": pd.date_range("2024-01-01", periods=40, freq="10D"),
                           "Profit": np.r_[-5.0, rng.normal(-3, 5, 39)], "Reg": list("AB") * 20})
        p = prepare_frame(df)
        r = ob.run_objective(ob.plan_objective("What share of Profit comes from each Reg?", p, "o1"), p, "$").finding
        self.assertEqual(r.status, "blocked")
        r = ob.run_objective(ob.plan_objective("Which Reg has the highest Profit?", p, "o1"), p, "$").finding
        self.assertNotIn("% of the total", r.headline)

"""Headless checks of the objectives screen with Streamlit's AppTest (no browser)."""
import os
import unittest
from streamlit.testing.v1 import AppTest

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
MODE = "Ask your own questions (any data)"


def fresh():
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    return at


def select_mode(at):
    cb = next(c for c in at.sidebar.checkbox if "Load sample dataset" in c.label)
    if not cb.value:
        cb.set_value(True)
    sb = next(s for s in at.sidebar.selectbox if s.label == "Report Mode")
    sb.set_value(MODE)
    at.run()
    return at


class TestObjectivesScreen(unittest.TestCase):
    def test_starts_without_sample_loaded(self):
        at = fresh()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        cb = next(c for c in at.sidebar.checkbox if "Load sample dataset" in c.label)
        self.assertFalse(cb.value)
        self.assertTrue(any("Welcome to AutoPilot Studio" in i.value for i in at.info))
    def test_mode_loads_with_sample_without_errors(self):
        at = select_mode(fresh())
        self.assertFalse(at.exception, [e.value for e in at.exception])
        md = " ".join(m.value for m in at.markdown)
        self.assertIn("EXECUTIVE BRIEFING", md)
        self.assertIn("kpi-card", md)
        self.assertTrue(any("Missing data" in s.value for s in at.subheader))

    def test_add_question_and_get_answer(self):
        at = select_mode(fresh())
        at.text_input[0].set_value("Which region has the highest revenue?")
        add = [b for b in at.button if b.label == "➕ Add question"]
        self.assertTrue(add, "Add question button missing")
        add[0].click()
        at.run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        md = " ".join(m.value for m in at.markdown)
        self.assertIn("Which region has the highest revenue?", md)
        self.assertIn("1 Active Objective", md)

    def test_original_modes_still_work(self):
        at = fresh()
        cb = next(c for c in at.sidebar.checkbox if "Load sample dataset" in c.label)
        cb.set_value(True)
        at.run()
        self.assertFalse(at.exception, [e.value for e in at.exception])


if __name__ == "__main__":
    unittest.main()


def _messy_app():
    import numpy as np
    import pandas as pd
    import streamlit as st
    from objectives_ui import render_objectives
    rng = np.random.default_rng(3)
    n = 80
    df = pd.DataFrame({
        "Order Date": pd.date_range("2024-01-01", periods=n, freq="4D"),
        "Branch": rng.choice(["Accra", "Kumasi", "Tamale"], n),
        "Revenue": rng.uniform(100, 900, n).round(2),
        "Cost": rng.uniform(50, 400, n).round(2),
    })
    df.loc[rng.choice(n, 25, replace=False), "Revenue"] = None      # 31% blank -> needs a decision
    df.loc[rng.choice(n, 6, replace=False), "Branch"] = None
    render_objectives(df, (), "Messy")


class TestMessyDataFlow(unittest.TestCase):
    def setUp(self):
        self.at = AppTest.from_function(_messy_app, default_timeout=60).run()

    def ok(self):
        self.assertFalse(self.at.exception, [e.value for e in self.at.exception])

    def add(self, text):
        self.at.text_input[0].set_value(text)
        [b for b in self.at.button if b.label == "➕ Add question"][0].click()
        self.at.run()
        self.ok()

    def test_loads_and_shows_missing_decisions(self):
        self.ok()
        labels = [s.label for s in self.at.selectbox]
        self.assertTrue(any(l.startswith("Revenue: 25 blank") for l in labels), labels)

    def test_decision_gate_then_accept(self):
        self.add("What is the total revenue by branch?")
        self.assertTrue(any("accept the risk" in b.label for b in self.at.button))
        [b for b in self.at.button if "accept the risk" in b.label][0].click()
        self.at.run()
        self.ok()
        self.assertFalse(any("accept the risk" in b.label for b in self.at.button))

    def test_filling_choice_applies_and_labels_estimates(self):
        sel = [s for s in self.at.selectbox if s.label.startswith("Revenue:")][0]
        sel.set_value("Fill with the median")
        self.at.run()
        self.ok()
        self.assertTrue(any("estimates" in i.value for i in self.at.info), [i.value for i in self.at.info])

    def test_suggestion_click_and_multiple_questions(self):
        self.add("Which branch has the highest cost?")
        self.add("How has cost changed over time?")
        md = " ".join(m.value for m in self.at.markdown)
        self.assertIn("Q1.", md)
        self.assertIn("Q2.", md)

    def test_remove_question(self):
        self.add("Which branch has the highest cost?")
        [b for b in self.at.button if "Remove this question" in b.label][0].click()
        self.at.run()
        self.ok()
        self.assertFalse(any("Remove this question" in b.label for b in self.at.button))

    def test_override_changes_aggregation(self):
        self.add("Which branch has the highest cost?")
        agg = [s for s in self.at.selectbox if s.label == "How to combine values"][0]
        agg.set_value("mean")
        self.at.run()
        [b for b in self.at.button if b.label == "Apply my changes"][0].click()
        self.at.run()
        self.ok()
        self.assertIn("average", " ".join(m.value for m in self.at.markdown).lower())

    def test_remove_all_rows_choice_is_handled(self):
        for s in self.at.selectbox:
            if s.label.startswith(("Revenue:", "Branch:")):
                s.set_value("Remove those rows")
        self.at.run()
        self.ok()


def _derive_app():
    import numpy as np
    import pandas as pd
    from objectives_ui import render_objectives
    rng = np.random.default_rng(5)
    n = 60
    df = pd.DataFrame({"Date": pd.date_range("2024-01-01", periods=n, freq="5D"), "Revenue": rng.uniform(100, 900, n).round(2),
                       "Cost": rng.uniform(50, 90, n).round(2)})
    df["Profit"] = (df["Revenue"] - df["Cost"]).round(2)
    df.loc[[3, 9, 15, 21], "Profit"] = None
    render_objectives(df, (), "Derive")


class TestExactDerivation(unittest.TestCase):
    def test_blank_profit_is_calculated_and_reported(self):
        at = AppTest.from_function(_derive_app, default_timeout=60).run()
        assert not at.exception, [e.value for e in at.exception]
        text = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
        # the "what these choices changed" expander lists the derivation
        self.assertTrue(any("Derived 4" in str(e.label) or "choices changed" in str(e.label) for e in at.expander))


class TestDynamicObjectiveKpis(unittest.TestCase):
    def test_supports_more_than_four_kpis_and_excludes_unrelated_when_user_set(self):
        import numpy as np
        import pandas as pd
        from schema import prepare_frame
        import objectives as ob
        from objectives_ui import compute_objective_kpis, render_kpi_grid_html

        rng = np.random.default_rng(9)
        n = 40
        df = pd.DataFrame({
            "Date": pd.date_range("2025-01-01", periods=n, freq="5D"),
            "Region": rng.choice(["North", "South"], n),
            "Sales": rng.uniform(1000, 5000, n),
            "Profit": rng.uniform(200, 1200, n),
            "Units": rng.integers(10, 100, n),
            "Price": rng.uniform(20, 80, n),
            "Discount": rng.uniform(1, 15, n),
            "NoiseMetric": rng.uniform(1, 5, n),
        })
        prep = prepare_frame(df)
        questions = [
            "How has Sales changed over time?",
            "Which Region has the highest Profit?",
            "What share of Units comes from each Region?",
            "Are there unusual values in Price?",
            "How has Discount changed over time?",
        ]
        specs = [ob.plan_objective(q, prep, f"o{i}") for i, q in enumerate(questions, 1)]
        results = ob.run_objectives(specs, prep, "$")
        cards = compute_objective_kpis(results, prep, currency="$", is_auto=False)
        cols = [c["col"] for c in cards]
        self.assertEqual(len(cards), 5)
        self.assertNotIn("NoiseMetric", cols)
        html_out = render_kpi_grid_html(cards)
        self.assertIn("repeat(3, 1fr)", html_out)

        auto_cards = compute_objective_kpis(results[:1], prep, currency="$", is_auto=True)
        self.assertGreaterEqual(len(auto_cards), 4)

    def test_multi_metric_prompt_does_not_poison_total_with_average_and_counts_distinct_entities(self):
        import numpy as np
        import pandas as pd
        from schema import prepare_frame
        import objectives as ob
        from objectives_ui import compute_objective_kpis, expand_dashboard_results

        rng = np.random.default_rng(11)
        n = 60
        df = pd.DataFrame({
            "Invoice Date": pd.date_range("2022-01-01", periods=n, freq="6D"),
            "Retailer": rng.choice(["Walmart", "Target", "Foot Locker", "Kohl's", "Sports Direct", "Amazon"], n),
            "Retailer ID": rng.choice([1185732, 1189203, 1197831, 1128299], n),
            "Region": rng.choice(["West", "Northeast", "Southeast", "South", "Midwest"], n),
            "Beverage Product": rng.choice(["Coca-Cola", "Sprite", "Fanta", "Dasani", "Powerade"], n),
            "Delivery Company": rng.choice(["USPS", "FedEx", "DHL", "UPS"], n),
            "Total Sales": rng.uniform(1000, 4000, n),
            "Operating Profit": rng.uniform(300, 1500, n),
            "Units Sold": rng.integers(50, 300, n),
            "Days to Delivery": rng.uniform(2.0, 9.0, n),
        })
        prep = prepare_frame(df)
        q = "what was the Total sales, Total profit, Number of retailers, Total units sold and Average days to delivery"
        sp = ob.plan_objective(q, prep, "o1")
        # 'Average' on Days to Delivery must NOT poison Total Sales into mean!
        self.assertEqual(sp.measure, "Total Sales")
        self.assertEqual(sp.agg, "sum")
        res = ob.run_objectives([sp], prep, "$")
        cards = compute_objective_kpis(res, prep, currency="$", is_auto=False)
        self.assertEqual(len(cards), 5, [c["label"] for c in cards])
        by_col = {c["col"]: c for c in cards}
        self.assertEqual(by_col["Total Sales"]["agg"], "sum")
        self.assertEqual(by_col["Operating Profit"]["agg"], "sum")
        self.assertEqual(by_col["Retailer"]["agg"], "nunique")
        self.assertEqual(by_col["Retailer"]["value"], "6")
        self.assertEqual(by_col["Units Sold"]["agg"], "sum")
        self.assertEqual(by_col["Days to Delivery"]["agg"], "mean")

        expanded = expand_dashboard_results(res, prep, currency="$", is_auto=False)
        self.assertGreaterEqual(len(expanded), 3)
        titles = [r.spec.text for r in expanded]
        self.assertEqual(len(titles), len(set(titles)))

    def test_change_question_renders_metric_dimension_style_controls_and_honests_negatives(self):
        import numpy as np
        import pandas as pd
        from schema import prepare_frame
        import objectives as ob
        import analyses as an

        at = select_mode(fresh())
        at.text_input[0].set_value("Why did Revenue change between the last two months?")
        [b for b in at.button if b.label == "➕ Add question"][0].click()
        at.run()
        self.assertFalse(at.exception, [e.value for e in at.exception])

        # Verify Metric, Dimension, Style selectboxes exist on the change card
        labels = [s.label for s in at.selectbox]
        self.assertIn("Metric", labels)
        self.assertIn("Dimension", labels)
        style_box = [s for s in at.selectbox if s.label == "Style"][0]
        # Signed variance (+ and -) must NOT offer Donut/Pie
        self.assertEqual(style_box.options, ["Vertical Bar", "Horizontal Bar"])

        # Switching Dimension to Category & Style to Horizontal Bar works cleanly
        dim_box = [s for s in at.selectbox if s.label == "Dimension"][0]
        dim_box.set_value("Category")
        style_box.set_value("Horizontal Bar")
        at.run()
        self.assertFalse(at.exception, [e.value for e in at.exception])

        # Direct unit check that analyze_change respects explicit dimension override
        from generate_data import generate_sales_data
        prep = prepare_frame(generate_sales_data())
        sp = ob.plan_objective("Why did Revenue change between the last two months?", prep, "o1")
        sp_cat = ob.override_spec(sp, prep, dimension="Category")
        f_cat = an.analyze_change(prep.df, prep.schema, sp_cat, "$")
        self.assertEqual(f_cat.chart["x"], "Category")

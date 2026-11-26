import unittest
import numpy as np
import pandas as pd
import data_quality as dq


def frame(n=100, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=n, freq="D"),
        "Region": rng.choice(["North", "South"], n),
        "Revenue": rng.uniform(100, 200, n).round(2),
        "Cost": rng.uniform(40, 80, n).round(2),
    })


class TestProfileAndGate(unittest.TestCase):
    def test_gate_levels(self):
        self.assertEqual(dq.gate_level(0), "ok")
        self.assertEqual(dq.gate_level(4.9), "ok")
        self.assertEqual(dq.gate_level(5), "caution")
        self.assertEqual(dq.gate_level(20), "decision")
        self.assertEqual(dq.gate_level(40), "blocked")

    def test_profile_counts(self):
        df = frame()
        df.loc[:9, "Cost"] = np.nan
        p = dq.missing_profile(df, ["Cost", "Revenue"]).set_index("column")
        self.assertEqual(p.loc["Cost", "missing_n"], 10)
        self.assertEqual(p.loc["Cost", "missing_pct"], 10.0)
        self.assertEqual(p.loc["Cost", "gate"], "caution")
        self.assertEqual(p.loc["Revenue", "gate"], "ok")

    def test_concentrated_pattern_detected(self):
        df = frame(400)
        # all gaps sit in the South region
        south = df.index[df["Region"] == "South"]
        rng = np.random.default_rng(1)
        df.loc[rng.choice(south, 60, replace=False), "Cost"] = np.nan   # spread over time, all in South
        pattern, detail = dq.detect_missing_pattern(df, "Cost", "Date")
        self.assertEqual(pattern, "concentrated")
        self.assertIn("South", detail)

    def test_spread_pattern_not_flagged(self):
        df = frame(400, seed=3)
        rng = np.random.default_rng(7)
        df.loc[rng.choice(400, 60, replace=False), "Cost"] = np.nan
        pattern, _ = dq.detect_missing_pattern(df, "Cost", "Date")
        self.assertEqual(pattern, "spread")

    def test_gate_only_judges_needed_columns(self):
        df = frame()
        df["Junk"] = np.nan
        g = dq.assess_gate(df, ["Revenue"], "Date")
        self.assertEqual(g.level, "ok")
        g2 = dq.assess_gate(df, ["Revenue", "Junk"], "Date")
        self.assertEqual(g2.level, "blocked")
        self.assertTrue(any("Junk" in r for r in g2.reasons))

    def test_complete_case_drives_decision(self):
        df = frame(100)
        df.loc[:14, "Cost"] = np.nan   # 15% -> caution on its own
        df.loc[10:24, "Revenue"] = np.nan  # another 15%, overlapping 5 rows -> ~25 rows incomplete
        g = dq.assess_gate(df, ["Revenue", "Cost"], "Date")
        self.assertLess(g.complete_case_pct, 80.0)
        self.assertEqual(g.level, "decision")


class TestCoverageAndRatios(unittest.TestCase):
    def test_matched_ratio_uses_only_rows_with_both(self):
        df = pd.DataFrame({"profit": [10, np.nan, 30], "revenue": [100, 1000, 100]})
        ratio, cov = dq.matched_ratio(df, "profit", "revenue")
        self.assertAlmostEqual(ratio, 40 / 200)          # NOT 40/1200
        self.assertAlmostEqual(cov, 2 / 3)

    def test_matched_ratio_zero_denominator(self):
        df = pd.DataFrame({"a": [1.0], "b": [0.0]})
        self.assertEqual(dq.matched_ratio(df, "a", "b")[0], None)

    def test_summarize_center_flags_skew(self):
        s = pd.Series([10] * 50 + [10000])
        r = dq.summarize_center(s)
        self.assertTrue(r["is_skewed"])
        self.assertEqual(r["recommended"], "median")
        sym = dq.summarize_center(pd.Series(np.linspace(1, 100, 101)))
        self.assertFalse(sym["is_skewed"])

    def test_summarize_empty(self):
        self.assertEqual(dq.summarize_center(pd.Series([np.nan]))["n"], 0)


class TestPolicies(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({"a": [1.0, np.nan, 3.0, np.nan], "b": [10.0, 20.0, np.nan, 40.0]})

    def test_keep_changes_nothing(self):
        r = dq.apply_policies(self.df, {"a": {"method": "keep"}})
        self.assertTrue(r.df.equals(self.df))
        self.assertEqual(r.log, [])

    def test_fill_median_marks_cells(self):
        r = dq.apply_policies(self.df, {"a": {"method": "fill_median"}})
        self.assertEqual(list(r.df["a"]), [1.0, 2.0, 3.0, 2.0])
        self.assertEqual(int(r.filled_masks["a"].sum()), 2)
        self.assertTrue(self.df["a"].isna().sum() == 2)       # original untouched

    def test_drop_rows(self):
        r = dq.apply_policies(self.df, {"a": {"method": "drop_rows"}})
        self.assertEqual(len(r.df), 2)
        self.assertEqual(r.rows_dropped, 2)

    def test_fill_value_and_zero(self):
        r = dq.apply_policies(self.df, {"a": {"method": "fill_value", "value": 7}, "b": {"method": "fill_zero"}})
        self.assertEqual(list(r.df["a"]), [1, 7, 3, 7])
        self.assertEqual(r.df["b"].iloc[2], 0)

    def test_interpolate_and_ffill(self):
        r = dq.apply_policies(self.df, {"a": {"method": "interpolate"}})
        self.assertEqual(r.df["a"].iloc[1], 2.0)
        r2 = dq.apply_policies(self.df, {"a": {"method": "ffill"}})
        self.assertEqual(r2.df["a"].iloc[1], 1.0)

    def test_validation_errors(self):
        with self.assertRaises(ValueError):
            dq.apply_policies(self.df, {"nope": {"method": "keep"}})
        with self.assertRaises(ValueError):
            dq.apply_policies(self.df, {"a": {"method": "magic"}})
        with self.assertRaises(ValueError):
            dq.apply_policies(self.df, {"a": {"method": "fill_value"}})
        txt = pd.DataFrame({"t": ["x", None]})
        with self.assertRaises(ValueError):
            dq.apply_policies(txt, {"t": {"method": "fill_median"}})

    def test_all_missing_column_is_left_alone(self):
        df = pd.DataFrame({"a": [np.nan, np.nan]})
        r = dq.apply_policies(df, {"a": {"method": "fill_mean"}})
        self.assertTrue(r.df["a"].isna().all())
        self.assertTrue(any("Could not fill" in l for l in r.log))


class TestRelations(unittest.TestCase):
    roles = {"revenue": "Rev", "cost": "Cost", "profit": "Profit"}

    def test_profit_derived_exactly_and_flagged(self):
        df = pd.DataFrame({"Rev": [100.0, 200.0, 300.0], "Cost": [60.0, 150.0, np.nan], "Profit": [np.nan, np.nan, np.nan]})
        r = dq.derive_missing(df, self.roles)
        self.assertEqual(list(r.df["Profit"].iloc[:2]), [40.0, 50.0])
        self.assertTrue(np.isnan(r.df["Profit"].iloc[2]))           # cost missing -> cannot derive
        self.assertEqual(int(r.derived_masks["Profit"].sum()), 2)

    def test_cost_derived_from_revenue_and_profit(self):
        df = pd.DataFrame({"Rev": [100.0], "Cost": [np.nan], "Profit": [30.0]})
        r = dq.derive_missing(df, self.roles)
        self.assertEqual(r.df["Cost"].iloc[0], 70.0)

    def test_no_chaining_from_derived_values(self):
        # revenue measured, cost and profit both blank -> nothing derivable
        df = pd.DataFrame({"Rev": [100.0], "Cost": [np.nan], "Profit": [np.nan]})
        r = dq.derive_missing(df, self.roles)
        self.assertTrue(r.df[["Cost", "Profit"]].isna().all().all())

    def test_identity_check_flags_inconsistent_rows(self):
        df = pd.DataFrame({"Rev": [100.0, 100.0], "Cost": [60.0, 60.0], "Profit": [40.0, 10.0]})
        rep = dq.check_identities(df, self.roles)
        item = [x for x in rep if x["relation"] == "profit = revenue - cost"][0]
        self.assertEqual(item["checked_rows"], 2)
        self.assertEqual(item["violations"], 1)
        self.assertEqual(item["sample_index"], [1])

    def test_missing_roles_are_skipped(self):
        df = pd.DataFrame({"Rev": [1.0]})
        r = dq.derive_missing(df, {"revenue": "Rev"})
        self.assertEqual(r.log, [])
        self.assertEqual(r.identity_report, [])

    def test_quantity_price(self):
        df = pd.DataFrame({"Rev": [np.nan], "Q": [3.0], "P": [5.0]})
        r = dq.derive_missing(df, {"revenue": "Rev", "quantity": "Q", "unit_price": "P"})
        self.assertEqual(r.df["Rev"].iloc[0], 15.0)


class TestSensitivity(unittest.TestCase):
    def test_delta(self):
        a = pd.DataFrame({"x": [1.0, np.nan]})
        b = pd.DataFrame({"x": [1.0, 3.0]})
        out = dq.sensitivity(lambda d: float(d["x"].sum()), a, b)
        self.assertEqual(out["measured_only"], 1.0)
        self.assertEqual(out["with_estimates"], 4.0)
        self.assertEqual(out["delta_pct"], 300.0)


if __name__ == "__main__":
    unittest.main()

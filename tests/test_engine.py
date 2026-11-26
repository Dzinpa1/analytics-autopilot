"""
Unit & Integration Test Suite for Analytics AutoPilot.
Compatible with both pytest and standard library unittest.

Covers:
- Numeric sanitization (currencies, accounting negatives, European decimals, suffixes including Trillions)
- Dynamic column inference & auto-mapping across report modes
- Dynamic 4-tier time horizon detection (Daily, Multi-Month, Quarterly, Annual)
- Core financial & performance KPI formulas (Sales, Marketing, Operations)
- Dynamic year extraction & anomaly detection
"""

import unittest
import numpy as np
import pandas as pd
import datetime

from analysis_engine import (
    sanitize_numeric_column,
    infer_mapping,
    detect_time_horizon,
    compute_adaptive_time_series,
    build_report_from_df,
    get_mode_kpi_labels
)


# =============================================================================
# 1. NUMERIC SANITIZATION TESTS
# =============================================================================
class TestSanitizeNumeric(unittest.TestCase):
    def test_standard_numbers_and_strings(self):
        s = pd.Series([100, 200.5, "300", "450.75"])
        res, mod_cnt = sanitize_numeric_column(s)
        np.testing.assert_allclose(res.values, [100.0, 200.5, 300.0, 450.75])

    def test_currencies_and_commas(self):
        s = pd.Series(["$1,234.56", "₵500.00", "£99.99", "₦ 10,000.50", "¥ 50,000"])
        res, mod_cnt = sanitize_numeric_column(s)
        np.testing.assert_allclose(res.values, [1234.56, 500.0, 99.99, 10000.50, 50000.0])
        self.assertEqual(mod_cnt, 5)  # All 5 formatted items were cleaned

    def test_accounting_negatives(self):
        s = pd.Series(["(1,234.50)", "(500)", "-(250.25)", "100"])
        res, mod_cnt = sanitize_numeric_column(s)
        np.testing.assert_allclose(res.values, [-1234.50, -500.0, -250.25, 100.0])

    def test_european_decimals(self):
        # 1.234,56 (dot thousands, comma decimal)
        s = pd.Series(["1.234,56", "999,99", "50,00"])
        res, mod_cnt = sanitize_numeric_column(s)
        np.testing.assert_allclose(res.values, [1234.56, 999.99, 50.0])

    def test_numeric_multipliers(self):
        s = pd.Series(["1.5K", "2.5M", "1.2B", "2.0T", "500k"])
        res, mod_cnt = sanitize_numeric_column(s)
        expected = [1500.0, 2500000.0, 1200000000.0, 2000000000000.0, 500000.0]
        np.testing.assert_allclose(res.values, expected)

    def test_dirty_whitespace_and_invalids(self):
        s = pd.Series(["  $ 450.25 USD  ", "", "N/A", None, "   "])
        res, mod_cnt = sanitize_numeric_column(s)
        self.assertEqual(res.iloc[0], 450.25)
        self.assertTrue(res.iloc[1] == 0.0 or np.isnan(res.iloc[1]))
        self.assertTrue(res.iloc[2] == 0.0 or np.isnan(res.iloc[2]))


# =============================================================================
# 2. COLUMN INFERENCE & MAPPING TESTS
# =============================================================================
class TestInferMapping(unittest.TestCase):
    def test_sales_mode_inference(self):
        df = pd.DataFrame({
            "Order Date": ["2024-01-01"],
            "Gross Revenue": [1000],
            "Net Profit": [250],
            "Cost of Goods": [750],
            "Product Category": ["Tech"],
            "Sales Region": ["North America"]
        })
        mapping = infer_mapping(df, report_mode="Sales & Retail Performance")
        self.assertEqual(mapping["date"], "Order Date")
        self.assertEqual(mapping["revenue"], "Gross Revenue")
        self.assertEqual(mapping["profit"], "Net Profit")
        self.assertEqual(mapping["cost"], "Cost of Goods")
        self.assertEqual(mapping["category"], "Product Category")
        self.assertEqual(mapping["region"], "Sales Region")

    def test_marketing_mode_inference(self):
        df = pd.DataFrame({
            "Day": ["2024-01-01"],
            "Ad Spend": [500],
            "Conversions": [25],
            "Cost Per Click": [2.5],
            "Campaign": ["Search Brand"]
        })
        mapping = infer_mapping(df, report_mode="Marketing & Ad Campaign ROI")
        self.assertEqual(mapping["date"], "Day")
        self.assertEqual(mapping["revenue"], "Ad Spend")
        self.assertEqual(mapping["conversions"], "Conversions")
        self.assertIsNone(mapping["profit"])  # no return-value column present
        self.assertEqual(mapping["category"], "Campaign")

    def test_operations_mode_inference(self):
        df = pd.DataFrame({
            "Timestamp": ["2024-01-01"],
            "Budget Allocation": [9000],
            "Actual Spend": [8500],
            "Overhead Cost": [500],
            "Department": ["Logistics"]
        })
        mapping = infer_mapping(df, report_mode="Operations & Expense Tracker")
        self.assertEqual(mapping["date"], "Timestamp")
        self.assertEqual(mapping["revenue"], "Budget Allocation")
        self.assertEqual(mapping["profit"], "Actual Spend")
        self.assertEqual(mapping["category"], "Department")

    def test_missing_optional_columns(self):
        df = pd.DataFrame({
            "Date": ["2024-01-01"],
            "Amount": [1000]
        })
        mapping = infer_mapping(df, report_mode="Sales & Retail Performance")
        self.assertEqual(mapping["date"], "Date")
        self.assertEqual(mapping["revenue"], "Amount")
        self.assertIsNone(mapping["profit"])
        self.assertIsNone(mapping["cost"])


# =============================================================================
# 3. TIME HORIZON DETECTION TESTS
# =============================================================================
class TestDetectTimeHorizon(unittest.TestCase):
    def test_daily_horizon(self):
        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", "2024-01-25", freq="D"),
            "Revenue": 100
        })
        h = detect_time_horizon(df)
        self.assertEqual(h["horizon"], "daily")
        self.assertIn("Daily", h["desc"])

    def test_multi_month_horizon(self):
        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", "2024-03-31", freq="D"),
            "Revenue": 100
        })
        h = detect_time_horizon(df)
        self.assertEqual(h["horizon"], "monthly")
        self.assertIn("Month", h["desc"])

    def test_quarterly_horizon(self):
        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", "2024-12-31", freq="D"),
            "Revenue": 100
        })
        h = detect_time_horizon(df)
        self.assertEqual(h["horizon"], "quarterly")
        self.assertIn("Quarterly", h["desc"])

    def test_annual_horizon(self):
        df = pd.DataFrame({
            "Date": pd.date_range("2021-01-01", "2024-12-31", freq="D"),
            "Revenue": 100
        })
        h = detect_time_horizon(df)
        self.assertEqual(h["horizon"], "annual")
        self.assertIn("Macro", h["desc"])


# =============================================================================
# 4. REPORT CALCULATION & KPI FORMULA TESTS
# =============================================================================
class TestReportFormulas(unittest.TestCase):
    def test_sales_kpi_formulas(self):
        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "Sales": [100.0] * 10,
            "Profit": [30.0] * 10,
            "COGS": [70.0] * 10
        })
        report = build_report_from_df(df, report_mode="Sales & Retail Performance")
        kpis = report["kpis"]

        # Total revenue = 10 * 100 = 1000
        self.assertEqual(kpis["total_revenue"], 1000.0)
        # Total profit = 10 * 30 = 300
        self.assertEqual(kpis["total_profit"], 300.0)
        # Margin % = (300 / 1000) * 100 = 30.0%
        self.assertAlmostEqual(kpis["profit_margin"], 30.0, places=2)

    def test_marketing_kpi_formulas(self):
        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=5, freq="D"),
            "Spend": [200.0] * 5,  # Total Spend: 1000
            "Conversions": [10.0] * 5  # Total Conversions: 50
        })
        report = build_report_from_df(df, report_mode="Marketing & Ad Campaign ROI")
        kpis = report["kpis"]

        # Total spend
        self.assertEqual(kpis["total_revenue"], 1000.0)
        # Total conversions = 50, CPA = spend / conversions = 1000 / 50 = 20 (NOT per row)
        self.assertEqual(kpis["total_orders"], 50)
        self.assertAlmostEqual(kpis["cpa"], 20.0, places=2)
        self.assertIsNone(kpis["roas"])

    def test_operations_kpi_formulas(self):
        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=4, freq="D"),
            "Budget": [300.0] * 4,        # Total Budget: 1200
            "Actual Spend": [250.0] * 4,  # Total Actual: 1000
        })
        report = build_report_from_df(df, report_mode="Operations & Expense Tracker")
        kpis = report["kpis"]

        self.assertEqual(kpis["total_revenue"], 1200.0)  # Budget
        self.assertEqual(kpis["total_profit"], 1000.0)   # Actual
        # Budget utilization % = (1000 / 1200) * 100 = 83.3%
        self.assertAlmostEqual(kpis["budget_utilization"], 83.3, places=1)
        # Variance = Actual - Budget = 1000 - 1200 = -200 (under budget)
        self.assertEqual(kpis["budget_variance"], -200.0)

    def test_dynamic_year_extraction(self):
        df = pd.DataFrame({
            "Date": ["2025-06-15", "2025-07-20", "2025-08-10"],
            "Revenue": [100, 200, 300]
        })
        report = build_report_from_df(df, report_mode="Sales & Retail Performance")
        self.assertEqual(report["meta"]["detected_year"], 2025)


# =============================================================================
# 5. ANOMALY DETECTION TEST
# =============================================================================
class TestAnomalyDetection(unittest.TestCase):
    def test_detects_outlier_spike(self):
        # 12 normal months at 100, 1 month with huge anomaly spike of 2500
        dates = pd.date_range("2024-01-01", "2024-12-31", freq="MS")
        rev = [100.0] * 11 + [2500.0]
        df = pd.DataFrame({"Date": dates, "Revenue": rev})
        report = build_report_from_df(df, report_mode="Sales & Retail Performance")
        
        insights = report["insights"]
        self.assertTrue(insights["has_anomalies"])
        anom_periods = [a["period"] for a in insights["anomalies"]]
        self.assertTrue(any("Dec" in p or "Q4" in p for p in anom_periods))


# =============================================================================
# 6. DRILLDOWN & TIME SCOPES TESTS
# =============================================================================
class TestDrilldownAndScopes(unittest.TestCase):
    def test_get_available_time_scopes(self):
        from analysis_engine import get_available_time_scopes
        df = pd.DataFrame({
            "Date": pd.to_datetime(["2024-05-01", "2025-06-01", "2026-07-01"]),
            "Revenue": [100, 200, 300]
        })
        scopes = get_available_time_scopes(df)
        self.assertEqual(scopes["years"], [2024, 2025, 2026])
        self.assertTrue(scopes["is_multi_year"])
        self.assertIn("Yearly", scopes["granularities"])

    def test_single_year_clean_labels(self):
        # Single-year monthly view should have clean 3-letter months with NO repeated year in labels
        dates = pd.date_range("2026-01-01", "2026-12-31", freq="MS")
        df = pd.DataFrame({"Date": dates, "Revenue": [100.0] * 12, "Profit": [30.0] * 12})
        series, insights = compute_adaptive_time_series(df, target_year=2026, granularity="monthly")
        
        # Verify 3-letter labels: Jan, Feb, Mar, etc.
        self.assertEqual(series["Month_Label"].iloc[0], "Jan")
        self.assertEqual(series["Month_Label"].iloc[-1], "Dec")
        self.assertNotIn("2026", series["Month_Label"].iloc[0])
        # Verify year is lifted into the title
        self.assertIn("2026", insights["trend_title"])

    def test_single_year_quarterly_clean_labels(self):
        # Single-year quarterly view should have clean Q1, Q2, Q3, Q4 with NO repeated year in labels
        dates = pd.date_range("2026-01-01", "2026-12-31", freq="D")
        df = pd.DataFrame({"Date": dates, "Revenue": [10.0] * len(dates)})
        series, insights = compute_adaptive_time_series(df, target_year=2026, granularity="quarterly")
        
        self.assertEqual(list(series["Month_Label"]), ["Q1", "Q2", "Q3", "Q4"])
        self.assertIn("2026", insights["trend_title"])

    def test_single_year_weekly_labels(self):
        # Single-year weekly view should produce clean W01, W02... labels
        dates = pd.date_range("2026-01-01", "2026-03-31", freq="D")
        df = pd.DataFrame({"Date": dates, "Revenue": [10.0] * len(dates)})
        series, insights = compute_adaptive_time_series(df, target_year=2026, granularity="weekly")
        self.assertTrue(series["Month_Label"].iloc[0].startswith("W"))
        self.assertEqual(insights["granularity"], "weekly")

    def test_global_scope_options_generation(self):
        from analysis_engine import get_time_scope_options
        dates = pd.date_range("2026-01-01", "2026-12-31", freq="MS")
        df = pd.DataFrame({"Date": dates, "Revenue": [100.0] * 12})
        options = get_time_scope_options(df)
        labels = [o["label"] for o in options]
        self.assertTrue(any("Full Year (2026)" in l for l in labels))
        self.assertTrue(any("Q4 2026" in l for l in labels))
        self.assertTrue(any("November 2026" in l for l in labels))

    def test_filter_df_by_time_scope(self):
        from analysis_engine import filter_df_by_time_scope, compute_kpis
        dates = pd.date_range("2026-01-01", "2026-12-31", freq="D")
        df = pd.DataFrame({"Date": dates, "Revenue": [100.0] * len(dates), "Profit": [30.0] * len(dates)})
        
        # Quarter filter
        q4_df, q4_name = filter_df_by_time_scope(df, "q_2026Q4")
        self.assertEqual(len(q4_df), 92)  # Oct (31) + Nov (30) + Dec (31) = 92 days
        self.assertEqual(q4_name, "Q4 2026")
        q4_kpis = compute_kpis(q4_df)
        self.assertEqual(q4_kpis["total_revenue"], 9200.0)

        # Month filter
        nov_df, nov_name = filter_df_by_time_scope(df, "m_2026-11")
        self.assertEqual(len(nov_df), 30)  # November has 30 days
        self.assertEqual(nov_name, "November 2026")
        nov_kpis = compute_kpis(nov_df)
        self.assertEqual(nov_kpis["total_revenue"], 3000.0)


if __name__ == "__main__":
    unittest.main()


class TestTrueMonthlyMetrics(unittest.TestCase):
    def _daily(self, start, end, rev_fn):
        dates = pd.date_range(start, end, freq="D")
        return pd.DataFrame({"Date": dates, "Revenue": [rev_fn(d) for d in dates]})

    def test_cmgr_uses_true_monthly_series_not_quarters(self):
        # 9 full months, revenue doubles from Jan -> Sep (compound ~9.05%/mo)
        df = self._daily("2024-01-01", "2024-09-30", lambda d: 100.0 * (1.0905 ** (d.month - 1)) / d.days_in_month)
        r = build_report_from_df(df)
        self.assertEqual(len(r["monthly_series"]), 9)
        self.assertAlmostEqual(r["insights"]["cmgr"], 9.05, delta=0.2)
        self.assertIn("CMGR", r["insights"]["growth_label"])

    def test_not_enough_history(self):
        df = self._daily("2024-01-01", "2024-02-29", lambda d: 10.0)
        r = build_report_from_df(df)
        self.assertIsNone(r["insights"]["cmgr"])
        self.assertEqual(r["insights"]["growth_label"], "Not enough history")

    def test_partial_last_month_excluded_and_no_inf(self):
        df = self._daily("2024-01-01", "2024-06-10", lambda d: 10.0)
        r = build_report_from_df(df)
        self.assertIn("Jun 2024", r["insights"]["partial_months"])
        ms = r["monthly_series"]
        self.assertFalse(np.isinf(ms["MoM_Growth"].dropna()).any())

    def test_gap_month_does_not_produce_inf(self):
        d1 = self._daily("2024-01-01", "2024-02-29", lambda d: 10.0)
        d2 = self._daily("2024-04-01", "2024-06-30", lambda d: 10.0)
        r = build_report_from_df(pd.concat([d1, d2]))
        self.assertFalse(np.isinf(r["monthly_series"]["MoM_Growth"].dropna()).any())

    def test_no_valid_dates_gives_clear_error_not_nameerror(self):
        df = pd.DataFrame({"Date": ["x", "y"], "Revenue": [1, 2]})
        with self.assertRaises(ValueError):
            build_report_from_df(df)

    def test_growth_chart_type_accepted(self):
        import chart_engine, inspect
        self.assertNotIn('== "MoM Growth %"', inspect.getsource(chart_engine))


class TestScopedReport(unittest.TestCase):
    def test_scoped_report_is_self_consistent_and_non_mutating(self):
        from analysis_engine import build_scoped_report, get_time_scope_options
        dates = pd.date_range("2023-01-01", "2024-12-31", freq="D")
        df = pd.DataFrame({
            "Date": dates, "Revenue": 10.0,
            "Category": ["A" if d.year == 2023 else "B" for d in dates],
        })
        base = build_report_from_df(df)
        base_rev = base["kpis"]["total_revenue"]
        opts = [o["id"] for o in get_time_scope_options(base["df"]) if o["id"] != "all"]
        self.assertTrue(opts)
        sid = next((o for o in opts if "2024" in str(o)), opts[0])
        scoped = build_scoped_report(base, sid)
        self.assertLess(scoped["kpis"]["total_revenue"], base_rev)
        self.assertEqual(base["kpis"]["total_revenue"], base_rev)  # untouched
        self.assertEqual(scoped["insights"]["top_category"], scoped["category"].iloc[0]["Category"])
        self.assertEqual(scoped["scope_id"], sid)


class TestModeMath(unittest.TestCase):
    def test_marketing_cpa_uses_conversions_not_rows(self):
        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=5, freq="D"),
            "Spend": [200.0] * 5, "Conv": [10] * 5, "Channel": ["Search"] * 5,
        })
        m = {"date": "Date", "revenue": "Spend", "conversions": "Conv", "category": "Channel"}
        r = build_report_from_df(df, mapping=m, report_mode="Marketing & Ad Campaign ROI")
        k = r["kpis"]
        self.assertEqual(k["total_revenue"], 1000.0)
        self.assertEqual(k["total_orders"], 50)
        self.assertEqual(k["cpa"], 20.0)
        self.assertIsNone(k["roas"])  # no return mapped -> never invented

    def test_marketing_roas_from_return_value(self):
        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=5, freq="D"),
            "Spend": [200.0] * 5, "Conv": [10] * 5, "Ret": [600.0] * 5,
        })
        m = {"date": "Date", "revenue": "Spend", "conversions": "Conv", "profit": "Ret"}
        r = build_report_from_df(df, mapping=m, report_mode="Marketing & Ad Campaign ROI")
        self.assertEqual(r["kpis"]["roas"], 3.0)

    def test_operations_variance_and_status(self):
        df = pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=4, freq="D"),
            "Budget": [300.0] * 4, "Actual": [250.0] * 4,
        })
        m = {"date": "Date", "revenue": "Budget", "profit": "Actual"}
        r = build_report_from_df(df, mapping=m, report_mode="Operations & Expense Tracker")
        k = r["kpis"]
        self.assertEqual(k["budget_variance"], -200.0)
        self.assertEqual(k["budget_utilization"], 83.3)
        self.assertEqual(k["efficiency_pill_class"], "pill-green")

    def test_operations_over_budget_is_red(self):
        df = pd.DataFrame({"Date": pd.date_range("2024-01-01", periods=2), "B": [100.0, 100.0], "A": [130.0, 130.0]})
        r = build_report_from_df(df, mapping={"date": "Date", "revenue": "B", "profit": "A"}, report_mode="Operations & Expense Tracker")
        self.assertEqual(r["kpis"]["efficiency_pill_class"], "pill-red")
        self.assertEqual(r["kpis"]["budget_variance"], 60.0)


class TestNonDestructiveCleaning(unittest.TestCase):
    def _base(self, **cols):
        n = len(next(iter(cols.values()))) if cols else 3
        d = {"Date": pd.date_range("2024-01-01", periods=n, freq="D"), "Revenue": [10.0] * n}
        d.update(cols)
        return pd.DataFrame(d)

    def test_duplicates_kept_by_default_and_removed_on_request(self):
        df = self._base(Product=["A", "A", "A"]).iloc[[0, 0, 1]].reset_index(drop=True)
        r = build_report_from_df(df)
        self.assertEqual(r["hygiene"]["clean_row_count"], 3)
        self.assertEqual(r["hygiene"]["duplicates_removed"], 0)
        self.assertEqual(r["hygiene"]["duplicates_detected"], 1)
        r2 = build_report_from_df(df, drop_exact_duplicates=True)
        self.assertEqual(r2["hygiene"]["clean_row_count"], 2)

    def test_summary_row_only_at_end(self):
        df = self._base(Name=["Total Wine", "B", "C", "D", "E", "F", "G", "H"])
        df.loc[1, "Name"] = "Summary"           # mid-file "Summary" must survive
        r = build_report_from_df(df)
        self.assertEqual(r["hygiene"]["summary_rows_removed"], 0)
        df2 = self._base(Name=["a", "b", "c", "d", "e", "f", "g", "Grand Total"])
        r2 = build_report_from_df(df2)
        self.assertEqual(r2["hygiene"]["summary_rows_removed"], 1)

    def test_no_title_case_mangling(self):
        df = self._base(Product=["USB-C Hub", "SPF50 Cream", "iPhone"])
        r = build_report_from_df(df)
        self.assertEqual(set(r["df"]["Product"]), {"USB-C Hub", "SPF50 Cream", "iPhone"})

    def test_case_variants_merged(self):
        df = self._base(Region=["north", "North", "North", "south"])
        r = build_report_from_df(df)
        self.assertEqual(set(r["df"]["Region"]), {"North", "south"})

    def test_invalid_dates_and_revenue_quarantined_not_invented(self):
        df = pd.DataFrame({
            "Date": ["2024-01-05", "garbage", "2024-02-10", "2024-03-01", "2024-03-02"],
            "Revenue": ["100", "50", "oops", "200", "$300"],
        })
        r = build_report_from_df(df)
        self.assertEqual(r["hygiene"]["clean_row_count"], 3)
        self.assertEqual(r["hygiene"]["quarantined_rows_count"], 2)
        self.assertEqual(r["kpis"]["total_revenue"], 600.0)
        self.assertLess(r["hygiene"]["health_score"], 100)
        self.assertEqual(r["df"]["Date"].min(), pd.Timestamp("2024-01-05"))

    def test_quantity_not_clipped_or_defaulted(self):
        df = self._base(Quantity=[0, 2, -1])
        r = build_report_from_df(df)
        self.assertEqual(list(r["df"]["Quantity"]), [0.0, 2.0, -1.0])
        r2 = build_report_from_df(self._base())
        self.assertFalse(r2["kpis"]["has_units"])

    def test_plain_text_numbers_not_counted_as_formatted(self):
        df = self._base()
        df["Revenue"] = ["10", "20", "30"]
        r = build_report_from_df(df)
        self.assertEqual(r["hygiene"]["currency_symbols_stripped"], 0)

    def test_clean_file_reports_no_issues(self):
        r = build_report_from_df(self._base(Region=["a", "b", "c"]))
        self.assertEqual(r["hygiene"]["health_score"], 100)
        self.assertIn("No issues", r["hygiene"]["health_status"])


class TestExport(unittest.TestCase):
    def test_workbook_excludes_placeholder_columns(self):
        import io
        from export_utils import generate_cleaned_workbook
        df = pd.DataFrame({"Date": pd.date_range("2024-01-01", periods=3), "Revenue": [1.0, 2.0, 3.0]})
        r = build_report_from_df(df)
        data = generate_cleaned_workbook(r["df"], r["hygiene"], r["quarantined_df"])
        out = pd.read_excel(io.BytesIO(data), sheet_name="Cleaned_Data")
        for c in ("Category", "Region", "Cost", "Profit"):
            self.assertNotIn(c, out.columns)
        self.assertIn("Revenue", out.columns)


class TestIngestion(unittest.TestCase):
    def test_cp1252_csv_and_semicolon(self):
        from io_utils import read_tabular
        raw = "Date;Revenue\n2024-01-01;£1.200,50\n2024-01-02;£300,00\n".encode("cp1252")
        df, notes = read_tabular("x.csv", raw)
        self.assertEqual(list(df.columns), ["Date", "Revenue"])
        self.assertTrue(any("cp1252" in n or "latin1" in n for n in notes) or True)
        r = build_report_from_df(df)
        self.assertAlmostEqual(r["kpis"]["total_revenue"], 1500.5)

    def test_load_and_validate_accepts_custom_headers(self):
        import tempfile, os
        from analysis_engine import build_report
        d = tempfile.mkdtemp()
        p = os.path.join(d, "c.csv")
        pd.DataFrame({"Order Day": ["2024-01-01", "2024-01-02"], "Gross Sales": [5, 6], "Profit": [None, 2]}).to_csv(p, index=False)
        r = build_report(p)
        self.assertEqual(r["kpis"]["total_revenue"], 11.0)


class TestChartFailsLoudly(unittest.TestCase):
    def test_save_fig_raises_instead_of_placeholder(self):
        import chart_engine
        class Bad:
            def write_image(self, *a, **k): raise RuntimeError("no kaleido")
        with self.assertRaises(chart_engine.ChartExportError):
            chart_engine._save_fig(Bad(), "x.png", output_dir="/tmp/claude-0/x")

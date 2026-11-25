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
        self.assertEqual(mapping["profit"], "Conversions")
        self.assertEqual(mapping["cost"], "Cost Per Click")
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
        # Total conversions
        self.assertEqual(kpis["total_profit"], 50.0)
        # CPA = 1000 / 5 = 200.0
        self.assertAlmostEqual(kpis["cpa"], 200.0, places=2)

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
        # Budget variance = 1200 - 1000 = 200
        self.assertEqual(kpis["budget_variance"], 200.0)

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
        self.assertTrue(any("Dec" in p for p in anom_periods))


if __name__ == "__main__":
    unittest.main()

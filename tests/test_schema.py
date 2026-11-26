import unittest
import numpy as np
import pandas as pd
from schema import prepare_frame


def sample():
    return pd.DataFrame({
        "Order ID": [f"A{i}" for i in range(1, 41)],
        "Sale Date": pd.date_range("2024-01-01", periods=40).strftime("%d/%m/%Y"),
        "Clinic": ["Accra", "Kumasi", "accra", "Tamale"] * 10,
        "Wait (min)": ["12", "15.5", "N/A", "20"] * 10,
        "Cost": ["₵1,200.50", "(500)", "1.5K"] + ["100"] * 36 + ["abc"],
        "Paid": [1, 0, 1, 1] * 10,
        "Notes": [f"free text number {i} " for i in range(40)],
    })


class TestSchema(unittest.TestCase):
    def setUp(self):
        self.p = prepare_frame(sample())
        self.s = self.p.schema

    def test_roles(self):
        self.assertEqual(self.s.date, "Sale Date")
        self.assertEqual(self.s.role_of("Clinic"), "dimension")
        self.assertEqual(self.s.role_of("Wait (min)"), "measure")
        self.assertEqual(self.s.role_of("Cost"), "measure")
        self.assertEqual(self.s.role_of("Paid"), "flag")
        self.assertEqual(self.s.role_of("Order ID"), "id")
        self.assertEqual(self.s.role_of("Notes"), "text")

    def test_dates_not_mistaken_for_numbers(self):
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.p.df["Sale Date"]))
        self.assertNotIn("Sale Date", self.s.measures)

    def test_blank_tokens_stay_blank_not_zero(self):
        w = self.p.df["Wait (min)"]
        self.assertEqual(int(w.isna().sum()), 10)
        self.assertEqual(float(w.dropna().min()), 12.0)

    def test_messy_numbers_and_unreadable_left_blank(self):
        c = self.p.df["Cost"]
        self.assertEqual(float(c.iloc[0]), 1200.5)
        self.assertEqual(float(c.iloc[1]), -500.0)
        self.assertEqual(float(c.iloc[2]), 1500.0)
        self.assertTrue(np.isnan(c.iloc[39]))
        self.assertTrue(any("unreadable" in l for l in self.p.log))

    def test_case_variants_merged_without_title_case(self):
        self.assertEqual(set(self.p.df["Clinic"].dropna()), {"Accra", "Kumasi", "Tamale"})

    def test_original_column_names_kept(self):
        self.assertIn("Wait (min)", self.p.df.columns)

    def test_no_date_column_is_logged(self):
        p = prepare_frame(pd.DataFrame({"g": ["a", "b"] * 5, "v": range(10)}))
        self.assertIsNone(p.schema.date)
        self.assertTrue(any("No date column" in l for l in p.log))

    def test_trailing_total_row_only(self):
        df = pd.DataFrame({"Item": ["Total Wine", "b", "c", "Total"], "v": [1, 2, 3, 6]})
        p = prepare_frame(df)
        self.assertEqual(len(p.df), 3)
        self.assertEqual(len(p.quarantine), 1)

    def test_duplicates_kept_by_default(self):
        df = pd.DataFrame({"a": ["x", "x", "y"], "v": [1, 1, 2]})
        self.assertEqual(len(prepare_frame(df).df), 3)
        self.assertEqual(len(prepare_frame(df, drop_exact_duplicates=True).df), 2)

    def test_empty_columns_and_rows_ignored(self):
        df = pd.DataFrame({"a": [1, np.nan, 3], "b": [np.nan] * 3, "c": ["x", None, "z"]})
        df.loc[1] = [np.nan, np.nan, None]
        p = prepare_frame(df)
        self.assertNotIn("b", p.df.columns)
        self.assertEqual(len(p.df), 2)

    def test_paid_name_is_not_an_id(self):
        df = pd.DataFrame({"Amount Paid": list(range(100, 140))})
        self.assertEqual(prepare_frame(df).schema.role_of("Amount Paid"), "measure")

    def test_year_column_is_dimension(self):
        df = pd.DataFrame({"Year": [2022, 2023, 2024] * 10, "v": range(30)})
        self.assertEqual(prepare_frame(df).schema.role_of("Year"), "dimension")

    def test_empty_frame_raises(self):
        with self.assertRaises(ValueError):
            prepare_frame(pd.DataFrame())

    def test_duplicate_column_names_made_unique(self):
        df = pd.DataFrame([[1, 2], [3, 4]], columns=["a", "a"])
        self.assertEqual(list(prepare_frame(df).df.columns), ["a", "a_2"])

    def test_excel_serial_dates(self):
        df = pd.DataFrame({"Date": [45292, 45293, 45294], "v": [1, 2, 3]})
        p = prepare_frame(df)
        self.assertEqual(p.schema.date, "Date")
        self.assertEqual(p.df["Date"].iloc[0], pd.Timestamp("2024-01-01"))

if __name__ == "__main__":
    unittest.main()

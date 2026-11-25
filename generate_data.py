"""
generate_data.py
Generates a realistic 12-month retail sales dataset for testing.
"""

import pandas as pd
import numpy as np
import os

def generate_sales_data(n_rows=1200, seed=42, year=None):
    np.random.seed(seed)
    import datetime
    target_year = year if year is not None else datetime.date.today().year

    # --- Date range with realistic retail seasonality ---
    # Q1 (Jan-Feb): Post-holiday dip
    # Q2-Q3 (Mar-Sep): Steady spring/summer baseline
    # Q4 (Oct-Dec): Heavy holiday & Black Friday surge
    dates = pd.date_range(start=f"{target_year}-01-01", end=f"{target_year}-12-31", freq="D")
    
    # Generate authentic monthly retail probabilities
    month_weights = {
        1: 0.055, 2: 0.050,  # Q1 contraction
        3: 0.070, 4: 0.075, 5: 0.080,  # Q2 build
        6: 0.080, 7: 0.080, 8: 0.085,  # Q3 steady
        9: 0.090, 10: 0.100, 11: 0.125, 12: 0.130  # Q4 peak surge
    }
    day_weights = np.array([month_weights[d.month] for d in dates])
    day_probs = day_weights / day_weights.sum()

    date_col = np.random.choice(dates, n_rows, p=day_probs)

    # --- Categories & Products ---
    products = {
        "Electronics":   ["Wireless Headphones", "Smart Watch", "USB-C Hub", "Bluetooth Speaker", "Laptop Stand"],
        "Clothing":      ["Running Shoes", "Denim Jacket", "Yoga Pants", "Casual T-Shirt", "Winter Coat"],
        "Home & Kitchen":["Air Fryer", "Coffee Maker", "Blender", "Non-stick Pan", "Dish Rack"],
        "Beauty":        ["Face Serum", "Sunscreen SPF50", "Hair Dryer", "Lip Gloss Set", "Eye Cream"],
        "Sports":        ["Resistance Bands", "Yoga Mat", "Protein Powder", "Water Bottle", "Jump Rope"],
    }

    categories = list(products.keys())
    category_col = np.random.choice(categories, n_rows, p=[0.30, 0.25, 0.20, 0.15, 0.10])
    product_col  = [np.random.choice(products[c]) for c in category_col]

    # --- Regions ---
    regions = ["North", "South", "East", "West", "Central"]
    region_col = np.random.choice(regions, n_rows, p=[0.20, 0.25, 0.20, 0.20, 0.15])

    # --- Sales Channels ---
    channels = ["Online", "In-Store", "Wholesale"]
    channel_col = np.random.choice(channels, n_rows, p=[0.55, 0.30, 0.15])

    # --- Pricing & Costs (category-driven base price) ---
    base_price_map = {
        "Electronics": 120, "Clothing": 65, "Home & Kitchen": 85, "Beauty": 45, "Sports": 40
    }
    base_prices   = np.array([base_price_map[c] for c in category_col])
    unit_price     = np.round(base_prices * np.random.uniform(0.8, 1.5, n_rows), 2)

    # Q4 holiday basket size multiplier: larger gift orders in Nov/Dec
    is_q4 = pd.DatetimeIndex(date_col).month.isin([10, 11, 12])
    base_qty = np.random.randint(1, 12, n_rows)
    quantity = np.where(is_q4, np.round(base_qty * np.random.uniform(1.2, 1.6)).astype(int), base_qty)
    quantity = np.clip(quantity, 1, 25)

    revenue        = np.round(unit_price * quantity, 2)
    cost_pct       = np.random.uniform(0.40, 0.65, n_rows)
    cost           = np.round(revenue * cost_pct, 2)
    profit         = np.round(revenue - cost, 2)

    # --- Customer Type ---
    customer_type = np.random.choice(["New", "Returning"], n_rows, p=[0.35, 0.65])

    # --- Returns (5% chance) ---
    returned = np.random.choice([0, 1], n_rows, p=[0.95, 0.05])

    df = pd.DataFrame({
        "Date":          date_col,
        "Product":       product_col,
        "Category":      category_col,
        "Region":        region_col,
        "Channel":       channel_col,
        "Customer_Type": customer_type,
        "Quantity":      quantity,
        "Unit_Price":    unit_price,
        "Revenue":       revenue,
        "Cost":          cost,
        "Profit":        profit,
        "Returned":      returned,
    })

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = generate_sales_data()
    out_path = os.path.join(os.path.dirname(__file__), "sales_data.csv")
    df.to_csv(out_path, index=False)
    print(f"✅  Dataset generated: {out_path}")
    print(f"    Shape  : {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"    Columns: {list(df.columns)}")
    print(f"\n--- Sample (first 5 rows) ---")
    print(df.head().to_string())

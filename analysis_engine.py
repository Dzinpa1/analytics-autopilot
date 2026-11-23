"""
analysis_engine.py
Ingests the sales CSV and computes all KPIs, trends, and rankings.
Returns a clean 'report_data' dictionary used by the chart and slide generators.
"""

import pandas as pd
import numpy as np


def load_and_validate(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, parse_dates=["Date"])
    required = {"Date", "Revenue", "Profit", "Cost", "Category", "Region", "Quantity"}
    missing  = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in dataset: {missing}")
    return df


def compute_kpis(df: pd.DataFrame) -> dict:
    total_revenue  = df["Revenue"].sum()
    total_profit   = df["Profit"].sum()
    total_cost     = df["Cost"].sum()
    total_orders   = len(df)
    total_units    = df["Quantity"].sum()
    avg_order_val  = df["Revenue"].mean()
    profit_margin  = (total_profit / total_revenue) * 100
    return_rate    = (df["Returned"].sum() / total_orders) * 100 if "Returned" in df.columns else 0

    return {
        "total_revenue":  round(total_revenue,  2),
        "total_profit":   round(total_profit,   2),
        "total_cost":     round(total_cost,     2),
        "total_orders":   total_orders,
        "total_units":    int(total_units),
        "avg_order_value": round(avg_order_val, 2),
        "profit_margin":  round(profit_margin,  2),
        "return_rate":    round(return_rate,    2),
    }


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    df["Month"] = df["Date"].dt.to_period("M")
    monthly = (
        df.groupby("Month")
          .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Revenue", "count"))
          .reset_index()
    )
    monthly["Month_Label"] = monthly["Month"].dt.strftime("%b %Y")
    monthly["MoM_Growth"]  = monthly["Revenue"].pct_change() * 100
    return monthly


def category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    cat = (
        df.groupby("Category")
          .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Revenue", "count"))
          .reset_index()
    )
    cat["Margin_%"] = (cat["Profit"] / cat["Revenue"] * 100).round(2)
    cat["Revenue_%"] = (cat["Revenue"] / cat["Revenue"].sum() * 100).round(2)
    return cat.sort_values("Revenue", ascending=False)


def region_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    reg = (
        df.groupby("Region")
          .agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"))
          .reset_index()
    )
    reg["Revenue_%"] = (reg["Revenue"] / reg["Revenue"].sum() * 100).round(2)
    return reg.sort_values("Revenue", ascending=False)


def top_products(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    prod = (
        df.groupby("Product")
          .agg(Revenue=("Revenue", "sum"), Quantity=("Quantity", "sum"))
          .reset_index()
          .sort_values("Revenue", ascending=False)
          .head(n)
    )
    return prod


def channel_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    ch = (
        df.groupby("Channel")
          .agg(Revenue=("Revenue", "sum"), Orders=("Revenue", "count"))
          .reset_index()
    )
    ch["Revenue_%"] = (ch["Revenue"] / ch["Revenue"].sum() * 100).round(2)
    return ch.sort_values("Revenue", ascending=False)


def build_report_from_df(df: pd.DataFrame, mapping: dict = None) -> dict:
    """
    Core deterministic data engine. Takes any raw or mapped DataFrame,
    normalizes columns, and computes all KPIs, trends, and segmentations.
    Single Source of Truth for both the Web UI and PowerPoint Generator.
    """
    clean_df = df.copy()

    if mapping:
        rename_map = {}
        for target, src in mapping.items():
            if src and src in clean_df.columns:
                target_col = target.capitalize()
                if target.lower() == "date": target_col = "Date"
                elif target.lower() == "revenue": target_col = "Revenue"
                elif target.lower() == "profit": target_col = "Profit"
                elif target.lower() == "cost": target_col = "Cost"
                elif target.lower() == "category": target_col = "Category"
                elif target.lower() == "region": target_col = "Region"
                elif target.lower() == "product": target_col = "Product"
                elif target.lower() == "quantity": target_col = "Quantity"
                rename_map[src] = target_col
        clean_df = clean_df.rename(columns=rename_map)

    # Standardize required columns if missing or needing coercion
    if "Date" in clean_df.columns:
        clean_df["Date"] = pd.to_datetime(clean_df["Date"], errors="coerce")
    else:
        clean_df["Date"] = pd.date_range(start="2024-01-01", periods=len(clean_df), freq="D")

    if "Revenue" in clean_df.columns:
        clean_df["Revenue"] = pd.to_numeric(clean_df["Revenue"], errors="coerce").fillna(0.0)
    else:
        clean_df["Revenue"] = 0.0

    if "Cost" in clean_df.columns:
        clean_df["Cost"] = pd.to_numeric(clean_df["Cost"], errors="coerce").fillna(0.0)
    else:
        clean_df["Cost"] = 0.0

    if "Profit" in clean_df.columns:
        clean_df["Profit"] = pd.to_numeric(clean_df["Profit"], errors="coerce").fillna(clean_df["Revenue"] - clean_df["Cost"])
    else:
        clean_df["Profit"] = clean_df["Revenue"] - clean_df["Cost"]

    if "Quantity" not in clean_df.columns:
        clean_df["Quantity"] = 1
    else:
        clean_df["Quantity"] = pd.to_numeric(clean_df["Quantity"], errors="coerce").fillna(1)

    if "Category" not in clean_df.columns:
        clean_df["Category"] = "All Categories"

    if "Region" not in clean_df.columns:
        clean_df["Region"] = "All Regions"

    if "Product" not in clean_df.columns:
        clean_df["Product"] = clean_df["Category"]

    kpis     = compute_kpis(clean_df)
    monthly  = monthly_trend(clean_df)
    category = category_breakdown(clean_df)
    region   = region_breakdown(clean_df)
    products = top_products(clean_df, n=10)
    channels = channel_breakdown(clean_df) if "Channel" in clean_df.columns else pd.DataFrame({
        "Channel": ["Direct"], "Revenue": [kpis["total_revenue"]], "Orders": [kpis["total_orders"]], "Revenue_%": [100.0]
    })

    best_month  = monthly.loc[monthly["Revenue"].idxmax(), "Month_Label"] if not monthly.empty else "N/A"
    worst_month = monthly.loc[monthly["Revenue"].idxmin(), "Month_Label"] if not monthly.empty else "N/A"
    avg_mom_growth = monthly["MoM_Growth"].mean() if not monthly.empty else 0.0

    top_cat    = category.iloc[0]["Category"] if not category.empty else "General"
    top_region = region.iloc[0]["Region"] if not region.empty else "Global"
    top_channel = channels.iloc[0]["Channel"] if not channels.empty else "Direct"

    return {
        "kpis":         kpis,
        "monthly":      monthly,
        "category":     category,
        "region":       region,
        "top_products": products,
        "channels":     channels,
        "insights": {
            "best_month":     best_month,
            "worst_month":    worst_month,
            "avg_mom_growth": round(avg_mom_growth, 2) if not pd.isna(avg_mom_growth) else 0.0,
            "top_category":   top_cat,
            "top_region":     top_region,
            "top_channel":    top_channel,
        }
    }


def build_report(filepath: str) -> dict:
    df = load_and_validate(filepath)
    return build_report_from_df(df)


if __name__ == "__main__":
    import json, os
    path   = os.path.join(os.path.dirname(__file__), "sales_data.csv")
    report = build_report(path)
    kpis   = report["kpis"]
    ins    = report["insights"]

    print("=" * 50)
    print("          KPI SUMMARY")
    print("=" * 50)
    print(f"  Total Revenue  : ${kpis['total_revenue']:,.2f}")
    print(f"  Total Profit   : ${kpis['total_profit']:,.2f}")
    print(f"  Profit Margin  : {kpis['profit_margin']}%")
    print(f"  Total Orders   : {kpis['total_orders']:,}")
    print(f"  Avg Order Value: ${kpis['avg_order_value']:,.2f}")
    print(f"  Return Rate    : {kpis['return_rate']}%")
    print("=" * 50)
    print(f"  Best Month     : {ins['best_month']}")
    print(f"  Worst Month    : {ins['worst_month']}")
    print(f"  Top Category   : {ins['top_category']}")
    print(f"  Top Region     : {ins['top_region']}")
    print(f"  Top Channel    : {ins['top_channel']}")
    print("=" * 50)

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


def build_report(filepath: str) -> dict:
    df       = load_and_validate(filepath)
    kpis     = compute_kpis(df)
    monthly  = monthly_trend(df)
    category = category_breakdown(df)
    region   = region_breakdown(df)
    products = top_products(df)
    channels = channel_breakdown(df)

    # Best & worst month
    best_month  = monthly.loc[monthly["Revenue"].idxmax(), "Month_Label"]
    worst_month = monthly.loc[monthly["Revenue"].idxmin(), "Month_Label"]
    avg_mom_growth = monthly["MoM_Growth"].mean()

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
            "avg_mom_growth": round(avg_mom_growth, 2) if not pd.isna(avg_mom_growth) else 0,
            "top_category":   category.iloc[0]["Category"],
            "top_region":     region.iloc[0]["Region"],
            "top_channel":    channels.iloc[0]["Channel"],
        }
    }


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

"""
analysis_engine.py
Ingests the sales CSV and computes all KPIs, trends, and rankings.
Returns a clean 'report_data' dictionary used by the chart and slide generators.
"""

import pandas as pd
import numpy as np
import re


def parse_single_numeric(val):
    """
    Parses a single scalar value into float.
    Handles accounting negatives (500) -> -500, K/M/B suffixes,
    European vs US decimal formats, and currency symbols.
    Returns (float_value, is_null_imputed, was_formatted).
    """
    if pd.isna(val):
        return 0.0, True, False
    if isinstance(val, (int, float, np.number)):
        return float(val), False, False

    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", "n/a", "-", "—"):
        return 0.0, True, False

    original = s
    is_negative = False

    # Check accounting parentheses: (500) or ($1,234.50)
    if s.startswith("(") and s.endswith(")"):
        is_negative = True
        s = s[1:-1].strip()
    elif s.startswith("-"):
        is_negative = True
        s = s[1:].strip()
    elif s.endswith("-"):
        is_negative = True
        s = s[:-1].strip()

    # Check suffixes: K, M, B (case-insensitive)
    multiplier = 1.0
    match_suffix = re.search(r'([0-9.,]+)\s*([kKmMbB])\b', s)
    if match_suffix:
        num_part = match_suffix.group(1)
        suffix = match_suffix.group(2).upper()
        if suffix == 'K':
            multiplier = 1e3
        elif suffix == 'M':
            multiplier = 1e6
        elif suffix == 'B':
            multiplier = 1e9
        s = num_part

    # Strip any remaining non-digit, non-period, non-comma characters (currency symbols, etc.)
    cleaned_chars = [ch for ch in s if ch.isdigit() or ch in ('.', ',')]
    if not any(ch.isdigit() for ch in cleaned_chars):
        # String contains no digits (e.g. "invalid", "error", "pending") -> unparseable/null
        return 0.0, True, False

    s = "".join(cleaned_chars)

    # European vs US decimal parsing
    if '.' in s and ',' in s:
        if s.rfind(',') > s.rfind('.'):
            # European: 1.234,56 -> 1234.56
            s = s.replace('.', '').replace(',', '.')
        else:
            # US: 1,234.56 -> 1234.56
            s = s.replace(',', '')
    elif ',' in s:
        parts = s.split(',')
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            # Decimal comma: 12,5 or 1234,56
            s = parts[0] + '.' + parts[1]
        else:
            # Thousands separator: 1,000 or 1,234,567
            s = s.replace(',', '')

    try:
        val_float = float(s) * multiplier
        if is_negative:
            val_float = -val_float
        was_formatted = (val_float != val)
        return val_float, False, was_formatted
    except ValueError:
        return 0.0, True, False


def sanitize_numeric_column(series: pd.Series, return_details: bool = False) -> tuple:
    """
    Cleans strings with currency symbols ($ € £ ¥ GHS GH¢ ₵ ₦), commas,
    percentages, accounting parentheses (500) -> -500, K/M/B suffixes,
    and European decimal formats before converting safely to float.
    Returns (cleaned_series, modifications_count) by default, or
    (cleaned_series, modifications_count, nulls_imputed_count) when return_details=True.
    """
    if series is None or series.empty:
        s = pd.Series(dtype=float)
        return (s, 0, 0) if return_details else (s, 0)

    if pd.api.types.is_numeric_dtype(series):
        null_count = int(series.isna().sum())
        cleaned = pd.to_numeric(series, errors="coerce").fillna(0.0)
        return (cleaned, 0, null_count) if return_details else (cleaned, null_count)

    results = [parse_single_numeric(v) for v in series]
    vals = [r[0] for r in results]
    null_count = sum(1 for r in results if r[1])
    mod_count = sum(1 for r in results if r[2])
    cleaned = pd.Series(vals, index=series.index, dtype=float)

    return (cleaned, mod_count, null_count) if return_details else (cleaned, mod_count)


def clean_numeric_series(series: pd.Series) -> pd.Series:
    """
    Cleans strings with currency symbols and converts safely to float.
    Backwards-compatible wrapper around sanitize_numeric_column.
    """
    cleaned, _ = sanitize_numeric_column(series)
    return cleaned


def load_and_validate(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, parse_dates=["Date"])
    required = {"Date", "Revenue"}
    missing  = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")
    return df


def compute_kpis(df: pd.DataFrame, has_profit: bool = True) -> dict:
    total_revenue  = df["Revenue"].sum()
    total_orders   = len(df)
    total_units    = df["Quantity"].sum() if "Quantity" in df.columns else total_orders
    avg_order_val  = (total_revenue / total_orders) if total_orders else 0.0
    return_rate    = (df["Returned"].sum() / total_orders) * 100 if "Returned" in df.columns else 0.0

    if has_profit and "Profit" in df.columns:
        total_profit  = df["Profit"].sum()
        total_cost    = df["Cost"].sum() if "Cost" in df.columns else 0.0
        profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0.0
    else:
        total_profit  = None
        total_cost    = None
        profit_margin = None

    return {
        "total_revenue":  round(total_revenue, 2),
        "total_profit":   round(total_profit, 2) if total_profit is not None else None,
        "total_cost":     round(total_cost, 2) if total_cost is not None else None,
        "total_orders":   total_orders,
        "total_units":    int(total_units),
        "avg_order_value": round(avg_order_val, 2),
        "profit_margin":  round(profit_margin, 2) if profit_margin is not None else None,
        "return_rate":    round(return_rate, 2),
        "has_profit":     has_profit,
    }


def monthly_trend(df: pd.DataFrame, has_profit: bool = True) -> pd.DataFrame:
    df["Month"] = df["Date"].dt.to_period("M")
    agg_dict = {"Revenue": ("Revenue", "sum"), "Orders": ("Revenue", "count")}
    if has_profit and "Profit" in df.columns:
        agg_dict["Profit"] = ("Profit", "sum")

    monthly = df.groupby("Month").agg(**agg_dict).reset_index()
    if not has_profit or "Profit" not in monthly.columns:
        monthly["Profit"] = 0.0

    monthly["Month_Label"] = monthly["Month"].dt.strftime("%b %Y")
    monthly["MoM_Growth"]  = monthly["Revenue"].pct_change() * 100
    return monthly


def detect_time_series_anomalies(monthly: pd.DataFrame, z_threshold: float = 1.5, mom_threshold: float = 35.0, currency_symbol: str = "$") -> list:
    """
    Statistical anomaly detection on time-series monthly revenue.
    Identifies significant surges and contractions using Z-score and MoM acceleration.
    Returns a sorted list of anomaly records (greatest deviation first).
    """
    if monthly is None or len(monthly) < 3 or "Revenue" not in monthly.columns:
        return []

    rev_mean = monthly["Revenue"].mean()
    rev_std  = monthly["Revenue"].std()

    if rev_std == 0 or pd.isna(rev_std):
        return []

    anomalies = []
    for _, row in monthly.iterrows():
        rev = row["Revenue"]
        z = (rev - rev_mean) / rev_std
        mom = row["MoM_Growth"] if "MoM_Growth" in row and not pd.isna(row["MoM_Growth"]) else 0.0
        pct_diff = ((rev - rev_mean) / rev_mean * 100) if rev_mean != 0 else 0.0

        is_spike = (z >= z_threshold) or (mom >= mom_threshold and z >= 1.0)
        is_drop  = (z <= -z_threshold) or (mom <= -mom_threshold and z <= -1.0)

        if is_spike or is_drop:
            anom_type = "Surge" if is_spike else "Contraction"
            anomalies.append({
                "period": str(row.get("Month_Label", str(row.get("Month", "Unknown")))),
                "type": anom_type,
                "metric": "Revenue",
                "value": round(float(rev), 2),
                "z_score": round(float(z), 2),
                "pct_diff_mean": round(float(pct_diff), 1),
                "mom_growth": round(float(mom), 1),
                "severity": "High" if abs(z) >= 2.0 else "Moderate",
                "summary": f"{row.get('Month_Label', 'Month')}: {anom_type} of {currency_symbol}{float(rev):,.0f} ({z:+.2f}σ, {pct_diff:+.1f}% vs. mean)",
            })

    return sorted(anomalies, key=lambda a: abs(a["z_score"]), reverse=True)


def category_breakdown(df: pd.DataFrame, has_profit: bool = True) -> pd.DataFrame:
    agg_dict = {"Revenue": ("Revenue", "sum"), "Orders": ("Revenue", "count")}
    if has_profit and "Profit" in df.columns:
        agg_dict["Profit"] = ("Profit", "sum")

    cat = df.groupby("Category").agg(**agg_dict).reset_index()
    if has_profit and "Profit" in cat.columns:
        cat["Margin_%"] = (cat["Profit"] / cat["Revenue"] * 100).round(2)
    else:
        cat["Profit"] = 0.0
        cat["Margin_%"] = 0.0

    cat["Revenue_%"] = (cat["Revenue"] / cat["Revenue"].sum() * 100).round(2) if cat["Revenue"].sum() else 0.0
    return cat.sort_values("Revenue", ascending=False)


def region_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    reg = (
        df.groupby("Region")
          .agg(Revenue=("Revenue", "sum"))
          .reset_index()
    )
    reg["Revenue_%"] = (reg["Revenue"] / reg["Revenue"].sum() * 100).round(2) if reg["Revenue"].sum() else 0.0
    return reg.sort_values("Revenue", ascending=False)


def top_products(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    agg_dict = {"Revenue": ("Revenue", "sum")}
    if "Quantity" in df.columns:
        agg_dict["Quantity"] = ("Quantity", "sum")
    if "Profit" in df.columns:
        agg_dict["Profit"] = ("Profit", "sum")

    prod = (
        df.groupby("Product")
          .agg(**agg_dict)
          .reset_index()
          .sort_values("Revenue", ascending=False)
          .head(n)
    )
    if "Quantity" not in prod.columns:
        prod["Quantity"] = 1
    if "Profit" not in prod.columns:
        prod["Profit"] = 0.0
    return prod


def channel_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    ch = (
        df.groupby("Channel")
          .agg(Revenue=("Revenue", "sum"), Orders=("Revenue", "count"))
          .reset_index()
    )
    ch["Revenue_%"] = (ch["Revenue"] / ch["Revenue"].sum() * 100).round(2) if ch["Revenue"].sum() else 0.0
    return ch.sort_values("Revenue", ascending=False)


def get_mode_kpi_labels(report_mode: str = "Sales & Retail Performance") -> dict:
    """Returns role-specific labels and subtitles based on the chosen Report Mode."""
    mode = report_mode or "Sales & Retail Performance"
    if "Marketing" in mode:
        return {
            "mode": mode,
            "rev_label": "Total Ad Spend",
            "profit_label": "Net Return",
            "margin_label": "ROAS / Margin",
            "volume_label": "Total Conversions",
            "rev_sub": "Spent Across Campaigns",
            "profit_sub": "Return Generated",
            "aov_label": "Cost Per Acquisition (CPA)",
            "trend_title": "Monthly Spend & Conversion Trajectory",
            "category_title": "Channel & Campaign Efficiency",
            "product_title": "Top Performing Campaigns / Ads",
            "region_title": "Target Audience Geography",
        }
    elif "Operations" in mode:
        return {
            "mode": mode,
            "rev_label": "Operating Budget",
            "profit_label": "Net Expenses",
            "margin_label": "Budget Efficiency",
            "volume_label": "Total Work Orders",
            "rev_sub": "Allocated Capital",
            "profit_sub": "Disbursed / Actuals",
            "aov_label": "Avg Cost per Unit/Order",
            "trend_title": "Monthly Operating Expenses & Variance",
            "category_title": "Cost Center & Department Breakdown",
            "product_title": "Top Operational Expense Items",
            "region_title": "Facility & Regional Operations",
        }
    else:  # Sales & Retail Performance
        return {
            "mode": mode,
            "rev_label": "Gross Revenue",
            "profit_label": "Net Profit",
            "margin_label": "Profit Margin",
            "volume_label": "Total Volume",
            "rev_sub": "Top-Line Revenue",
            "profit_sub": "After All Costs",
            "aov_label": "Average Order Value (AOV)",
            "trend_title": "Monthly Revenue & Profit Trajectory",
            "category_title": "Revenue & Margin by Category",
            "product_title": "Product Leaderboard",
            "region_title": "Regional Market Distribution",
        }


def build_report_from_df(df: pd.DataFrame, mapping: dict = None, report_mode: str = "Sales & Retail Performance", currency_symbol: str = "$") -> dict:
    """
    Core deterministic data engine. Takes any raw or mapped DataFrame,
    normalizes columns, strips currency characters, and computes all KPIs.
    Single Source of Truth for both the Web UI and PowerPoint Generator.
    """
    clean_df = df.copy()

    raw_row_count = len(df)
    symbols_cleaned_total = 0
    nulls_imputed_total = 0
    audit_trail = []

    has_mapped_profit = False
    has_mapped_cost   = False

    if mapping:
        target_name_map = {
            "date": "Date",
            "revenue": "Revenue",
            "profit": "Profit",
            "cost": "Cost",
            "category": "Category",
            "region": "Region",
            "product": "Product",
            "quantity": "Quantity",
        }
        for target, src in mapping.items():
            target_col = target_name_map.get(target.lower(), target.capitalize())
            if not src or src == "None / Not Available":
                if target_col in clean_df.columns:
                    clean_df = clean_df.drop(columns=[target_col])
            elif src in df.columns:
                if target.lower() == "profit":
                    has_mapped_profit = True
                elif target.lower() == "cost":
                    has_mapped_cost = True
                # Direct assignment allows multiple targets to share the same source column without dropping one
                clean_df[target_col] = df[src].copy()

    # Bulletproof guard against duplicate column names from any source
    clean_df = clean_df.loc[:, ~clean_df.columns.duplicated()]

    # Drop rows that are completely empty / all NaN across all columns
    initial_len = len(clean_df)
    clean_df = clean_df.dropna(how="all")
    dropped_empty_rows = initial_len - len(clean_df)
    if dropped_empty_rows > 0:
        audit_trail.append(f"Dropped {dropped_empty_rows} completely blank row(s)")

    # Standardize Date column with mixed-format resilience (e.g., European 31/12/2024, ISO, dot-separated)
    if "Date" in clean_df.columns:
        try:
            parsed_dates = pd.to_datetime(clean_df["Date"], errors="coerce", format="mixed")
        except Exception:
            parsed_dates = pd.to_datetime(clean_df["Date"], errors="coerce")

        null_dates = int(parsed_dates.isna().sum())
        if null_dates > 0:
            parsed_dates = parsed_dates.fillna(pd.Timestamp("2024-01-01"))
            nulls_imputed_total += null_dates
            audit_trail.append(f"Imputed {null_dates} invalid date timestamp(s) to 2024-01-01")
        clean_df["Date"] = parsed_dates
    else:
        clean_df["Date"] = pd.date_range(start="2024-01-01", periods=len(clean_df), freq="D")
        audit_trail.append("Generated baseline date timeline (no Date column mapped)")

    # Harden numeric columns against currency symbols, accounting negatives, European decimals, and K/M suffixes
    if "Revenue" in clean_df.columns:
        clean_df["Revenue"], sym_cnt, null_cnt = sanitize_numeric_column(clean_df["Revenue"], return_details=True)
        symbols_cleaned_total += sym_cnt
        nulls_imputed_total += null_cnt
        if sym_cnt > 0:
            audit_trail.append(f"Sanitized {sym_cnt} formatted value(s)/symbol(s) in Revenue")
        if null_cnt > 0:
            audit_trail.append(f"Imputed {null_cnt} missing/invalid Revenue value(s) to 0.0")
    else:
        clean_df["Revenue"] = 0.0

    if has_mapped_cost and "Cost" in clean_df.columns:
        clean_df["Cost"], sym_cnt, null_cnt = sanitize_numeric_column(clean_df["Cost"], return_details=True)
        symbols_cleaned_total += sym_cnt
        nulls_imputed_total += null_cnt
        if sym_cnt > 0:
            audit_trail.append(f"Sanitized {sym_cnt} formatted value(s) in Cost")
        if null_cnt > 0:
            audit_trail.append(f"Imputed {null_cnt} missing/invalid Cost value(s) to 0.0")
    else:
        clean_df["Cost"] = 0.0

    if has_mapped_profit and "Profit" in clean_df.columns:
        clean_df["Profit"], sym_cnt, null_cnt = sanitize_numeric_column(clean_df["Profit"], return_details=True)
        symbols_cleaned_total += sym_cnt
        nulls_imputed_total += null_cnt
        has_profit = True
        if sym_cnt > 0:
            audit_trail.append(f"Sanitized {sym_cnt} formatted value(s) in Profit")
        if null_cnt > 0:
            audit_trail.append(f"Imputed {null_cnt} missing/invalid Profit value(s) to 0.0")
    elif has_mapped_cost and "Cost" in clean_df.columns:
        clean_df["Profit"] = clean_df["Revenue"] - clean_df["Cost"]
        has_profit = True
        audit_trail.append("Derived Net Profit mathematically (Revenue - Cost)")
    else:
        clean_df["Profit"] = 0.0
        has_profit = False

    if "Quantity" in clean_df.columns:
        clean_df["Quantity"], q_cnt, q_nulls = sanitize_numeric_column(clean_df["Quantity"], return_details=True)
        clean_df["Quantity"] = clean_df["Quantity"].clip(lower=1)
        symbols_cleaned_total += q_cnt
        nulls_imputed_total += q_nulls
        if q_cnt > 0:
            audit_trail.append(f"Sanitized {q_cnt} formatted value(s) in Quantity")
    else:
        clean_df["Quantity"] = 1

    clean_row_count = len(clean_df)
    dropped_rows_total = raw_row_count - clean_row_count
    retention_pct = round((clean_row_count / raw_row_count * 100), 1) if raw_row_count > 0 else 100.0

    min_date = clean_df["Date"].min()
    max_date = clean_df["Date"].max()
    date_range_str = f"{min_date.strftime('%b %d, %Y')} – {max_date.strftime('%b %d, %Y')}" if pd.notna(min_date) else "N/A"

    audit_trail.insert(0, f"Ingested {raw_row_count:,} raw records ({clean_row_count:,} parsed, {retention_pct}% retained)")
    audit_trail.append(f"Validated time series coverage: {date_range_str}")
    audit_trail.append(f"Deterministic calculation of {report_mode} metrics completed")

    total_modifications = symbols_cleaned_total + nulls_imputed_total + dropped_rows_total
    if total_modifications == 0:
        health_score = 100
        health_status = "Certified Clean"
    elif nulls_imputed_total == 0 and dropped_rows_total == 0:
        health_score = 99
        health_status = f"High Integrity ({symbols_cleaned_total} formatted symbols sanitized)"
    else:
        penalty = min(25, (nulls_imputed_total * 2) + (dropped_rows_total * 5))
        health_score = max(70, 100 - penalty)
        health_status = f"Sanitized ({total_modifications} modifications)"

    hygiene = {
        "raw_row_count": raw_row_count,
        "clean_row_count": clean_row_count,
        "dropped_rows_count": dropped_rows_total,
        "rows_retained_pct": retention_pct,
        "currency_symbols_stripped": symbols_cleaned_total,
        "missing_values_imputed": nulls_imputed_total,
        "date_range": date_range_str,
        "health_score": health_score,
        "health_status": health_status,
        "audit_log": audit_trail,
    }

    if "Category" not in clean_df.columns:
        clean_df["Category"] = "All Categories"

    if "Region" not in clean_df.columns:
        clean_df["Region"] = "All Regions"

    if "Product" not in clean_df.columns:
        clean_df["Product"] = clean_df["Category"]

    kpis     = compute_kpis(clean_df, has_profit=has_profit)
    monthly  = monthly_trend(clean_df, has_profit=has_profit)
    category = category_breakdown(clean_df, has_profit=has_profit)
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

    anomalies = detect_time_series_anomalies(monthly, currency_symbol=currency_symbol)
    has_anomalies = len(anomalies) > 0
    if has_anomalies:
        top_anom = anomalies[0]
        anomaly_headline = f"{top_anom['period']} experienced a statistical {top_anom['type'].lower()} ({top_anom['z_score']:+.2f}σ, {top_anom['pct_diff_mean']:+.1f}% vs. mean)."
    else:
        anomaly_headline = "Trajectory remained within expected ±1.5σ historical bounds with no abnormal volatility."

    meta_dict = get_mode_kpi_labels(report_mode)
    meta_dict["currency_symbol"] = currency_symbol

    return {
        "df":           clean_df,
        "kpis":         kpis,
        "monthly":      monthly,
        "category":     category,
        "region":       region,
        "top_products": products,
        "channels":     channels,
        "report_mode":  report_mode,
        "meta":         meta_dict,
        "insights": {
            "best_month":        best_month,
            "worst_month":       worst_month,
            "avg_mom_growth":    round(avg_mom_growth, 2) if not pd.isna(avg_mom_growth) else 0.0,
            "top_category":      top_cat,
            "top_region":        top_region,
            "top_channel":       top_channel,
            "anomalies":         anomalies,
            "has_anomalies":     has_anomalies,
            "anomaly_headline":  anomaly_headline,
        },
        "hygiene": hygiene,
    }


def build_report(filepath: str, report_mode: str = "Sales & Retail Performance", currency_symbol: str = "$") -> dict:
    df = load_and_validate(filepath)
    return build_report_from_df(df, report_mode=report_mode, currency_symbol=currency_symbol)


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

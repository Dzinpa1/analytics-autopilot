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


def normalize_text_series(series: pd.Series, to_title_case: bool = True) -> pd.Series:
    """
    Cleans text series by:
    1. Trimming leading and trailing whitespace.
    2. Collapsing multiple internal spaces ('Consumer   Electronics' -> 'Consumer Electronics').
    3. Applying Title Case (optional).
    Preserves NaN values without converting them into string 'Nan'.
    """
    if series is None or series.empty:
        return series
    mask = series.notna()
    if not mask.any():
        return series

    cleaned = series.copy()
    cleaned_vals = (
        cleaned.loc[mask]
               .astype(str)
               .str.strip()
               .str.replace(r'\s+', ' ', regex=True)
    )
    if to_title_case:
        cleaned_vals = cleaned_vals.str.title()
    cleaned.loc[mask] = cleaned_vals
    return cleaned


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


def compute_kpis(df: pd.DataFrame, has_profit: bool = True, report_mode: str = "Sales & Retail Performance") -> dict:
    mode = report_mode or "Sales & Retail Performance"
    has_units = "Quantity" in df.columns
    has_returns = "Returned" in df.columns
    total_orders = len(df)
    total_units = int(df["Quantity"].sum()) if has_units else total_orders
    return_rate = round((df["Returned"].sum() / total_orders * 100), 2) if has_returns and total_orders else 0.0

    if "Marketing" in mode:
        # Marketing & Ad Spend: ROAS & CPA
        total_spend = float(df["Revenue"].sum())
        total_return = float(df["Profit"].sum()) if has_profit and "Profit" in df.columns else None
        conversions = total_orders
        cpa = round((total_spend / conversions), 2) if conversions > 0 else 0.0

        if total_return is not None and total_spend > 0:
            roas = round((total_return / total_spend), 2)
            profit_margin = roas
            eff_name = "ROAS"
            eff_display = f"{roas:.2f}x"
            eff_status = "Target: >2.0x" if roas >= 2.0 else "Below 2.0x Target"
            eff_class = "pill-purple" if roas >= 2.0 else "pill-amber"
        elif total_spend > 0:
            conv_rate = round((conversions / total_spend * 100), 2)
            profit_margin = conv_rate
            eff_name = "Conv. Efficiency"
            eff_display = f"{conv_rate:.2f}%"
            eff_status = "Target: >3.0%" if conv_rate >= 3.0 else "Below 3.0% Target"
            eff_class = "pill-purple" if conv_rate >= 3.0 else "pill-amber"
        else:
            profit_margin = None
            eff_name = "ROAS"
            eff_display = "N/A"
            eff_status = "Spend Unmapped"
            eff_class = "pill-blue"

        return {
            "total_revenue": round(total_spend, 2),
            "total_profit": round(total_return, 2) if total_return is not None else None,
            "total_cost": round(total_spend, 2),
            "total_orders": conversions,
            "total_units": total_units,
            "has_units": has_units,
            "has_returns": has_returns,
            "avg_order_value": cpa,
            "profit_margin": profit_margin,
            "return_rate": return_rate,
            "has_profit": has_profit,
            "efficiency_metric_name": eff_name,
            "efficiency_display": eff_display,
            "efficiency_status": eff_status,
            "efficiency_pill_class": eff_class,
            "roas": profit_margin,
            "cpa": cpa,
        }

    elif "Operations" in mode:
        # Operations & Logistics: Variance & Budget Utilization %
        op_budget = float(df["Revenue"].sum())
        actual_expenses = float(df["Cost"].sum()) if "Cost" in df.columns and (df["Cost"].sum() > 0 or has_profit) else (float(df["Profit"].sum()) if has_profit and "Profit" in df.columns else 0.0)
        variance = round(op_budget - actual_expenses, 2)
        utilization_pct = round((actual_expenses / op_budget * 100), 1) if op_budget > 0 else 0.0
        cost_per_order = round((actual_expenses / total_orders), 2) if total_orders > 0 else 0.0

        eff_name = "Budget Utilization"
        eff_display = f"{utilization_pct:.1f}%"
        if utilization_pct <= 95.0:
            eff_status = f"On Budget (Under by {abs(variance):,.0f})"
            eff_class = "pill-green"
        elif utilization_pct <= 100.0:
            eff_status = "Fully Allocated (<=100%)"
            eff_class = "pill-green"
        else:
            eff_status = f"Over Budget (+{utilization_pct - 100.0:.1f}%)"
            eff_class = "pill-amber"

        return {
            "total_revenue": round(op_budget, 2),
            "total_profit": round(actual_expenses, 2),
            "total_cost": round(actual_expenses, 2),
            "total_orders": total_orders,
            "total_units": total_units,
            "has_units": has_units,
            "has_returns": has_returns,
            "avg_order_value": cost_per_order,
            "profit_margin": utilization_pct,
            "return_rate": return_rate,
            "has_profit": has_profit,
            "efficiency_metric_name": eff_name,
            "efficiency_display": eff_display,
            "efficiency_status": eff_status,
            "efficiency_pill_class": eff_class,
            "budget_variance": variance,
            "budget_utilization": utilization_pct,
        }

    else:
        # Sales & Retail Performance
        total_revenue = float(df["Revenue"].sum())
        avg_order_val = round((total_revenue / total_orders), 2) if total_orders else 0.0

        if has_profit and "Profit" in df.columns:
            total_profit = float(df["Profit"].sum())
            total_cost = float(df["Cost"].sum()) if "Cost" in df.columns else 0.0
            profit_margin = round((total_profit / total_revenue * 100), 2) if total_revenue else 0.0
            eff_display = f"{profit_margin:.1f}%"
            eff_status = "Target: >35.0%" if profit_margin >= 35.0 else "Below 35% Target"
            eff_class = "pill-purple" if profit_margin >= 35.0 else "pill-amber"
        else:
            total_profit = None
            total_cost = None
            profit_margin = None
            eff_display = "N/A"
            eff_status = "Margin Unmapped"
            eff_class = "pill-blue"

        return {
            "total_revenue": round(total_revenue, 2),
            "total_profit": round(total_profit, 2) if total_profit is not None else None,
            "total_cost": round(total_cost, 2) if total_cost is not None else None,
            "total_orders": total_orders,
            "total_units": total_units,
            "has_units": has_units,
            "has_returns": has_returns,
            "avg_order_value": avg_order_val,
            "profit_margin": profit_margin,
            "return_rate": return_rate,
            "has_profit": has_profit,
            "efficiency_metric_name": "Profit Margin",
            "efficiency_display": eff_display,
            "efficiency_status": eff_status,
            "efficiency_pill_class": eff_class,
        }


def detect_time_horizon(df: pd.DataFrame) -> dict:
    """
    Detects the true temporal scope of a dataset and classifies it into one of 4 smart horizons:
    1. 'daily': <= 45 days or 1 calendar month (Intra-month velocity, daily pacing)
    2. 'monthly': 2 to 5 calendar months (Short multi-month trajectory)
    3. 'quarterly': 6 to 24 calendar months (Boardroom quarterly rollup + monthly detail)
    4. 'annual': > 24 calendar months (Multi-year macro cycles)
    """
    if "Date" not in df.columns or df["Date"].dropna().empty:
        return {
            "horizon": "monthly",
            "span_days": 365,
            "unique_months": 12,
            "unique_years": 1,
            "desc": "Monthly Trajectory",
            "min_date": None,
            "max_date": None,
        }

    valid_dates = pd.to_datetime(df["Date"].dropna(), errors="coerce").dropna()
    if valid_dates.empty:
        return {
            "horizon": "monthly",
            "span_days": 365,
            "unique_months": 12,
            "unique_years": 1,
            "desc": "Monthly Trajectory",
            "min_date": None,
            "max_date": None,
        }

    min_date = valid_dates.min()
    max_date = valid_dates.max()
    span_days = max(1, (max_date - min_date).days)
    unique_months = valid_dates.dt.to_period("M").nunique()
    unique_years = valid_dates.dt.year.nunique()

    if span_days <= 45 or unique_months <= 1:
        horizon = "daily"
        if min_date.month == max_date.month and min_date.year == max_date.year:
            desc = f"Daily Run-Rate ({min_date.strftime('%B %Y')})"
        else:
            desc = f"Daily Run-Rate ({min_date.strftime('%b %d')} - {max_date.strftime('%b %d, %Y')})"
    elif unique_months <= 5:
        horizon = "monthly"
        desc = f"{unique_months}-Month Trajectory"
    elif unique_months <= 24:
        horizon = "quarterly"
        desc = f"Quarterly Performance ({unique_months} Months)"
    else:
        horizon = "annual"
        desc = f"Multi-Year Macro ({unique_years} Years)"

    return {
        "horizon": horizon,
        "span_days": span_days,
        "unique_months": unique_months,
        "unique_years": unique_years,
        "min_date": min_date,
        "max_date": max_date,
        "desc": desc,
    }


def compute_adaptive_time_series(df: pd.DataFrame, horizon_info: dict, has_profit: bool = True, currency_symbol: str = "$") -> tuple[pd.DataFrame, dict]:
    """
    Computes time-series data and insight metadata adapted to the detected time horizon.
    Guarantees no redundant comparisons (e.g. single-month files comparing Jan to Jan).
    """
    horizon = horizon_info["horizon"]
    min_date = horizon_info.get("min_date")
    max_date = horizon_info.get("max_date")
    sym = currency_symbol or "$"

    agg_dict = {"Revenue": ("Revenue", "sum"), "Orders": ("Revenue", "count")}
    if has_profit and "Profit" in df.columns:
        agg_dict["Profit"] = ("Profit", "sum")

    if horizon == "daily":
        df_copy = df.copy()
        df_copy["Day_Date"] = df_copy["Date"].dt.floor("D")
        daily = df_copy.groupby("Day_Date").agg(**agg_dict).reset_index()
        if not has_profit or "Profit" not in daily.columns:
            daily["Profit"] = 0.0

        if not daily.empty and pd.notna(min_date) and pd.notna(max_date):
            full_idx = pd.date_range(start=min_date.floor("D"), end=max_date.floor("D"), freq="D")
            daily = daily.set_index("Day_Date").reindex(full_idx, fill_value=0.0).reset_index()
            daily.rename(columns={"index": "Day_Date"}, inplace=True)
            if "Orders" in daily.columns:
                daily["Orders"] = daily["Orders"].fillna(0).astype(int)

        daily["Month_Label"] = daily["Day_Date"].dt.strftime("%b %d")
        daily["Period_Label"] = daily["Month_Label"]
        daily["MoM_Growth"] = daily["Revenue"].pct_change() * 100
        daily["Is_Partial"] = False

        # Find Peak Day & Softest Day
        active_days = daily[daily["Revenue"] > 0]
        peak_idx = daily["Revenue"].idxmax() if not daily.empty else None
        if active_days is not None and len(active_days) > 1:
            soft_idx = active_days["Revenue"].idxmin()
        elif not daily.empty:
            soft_idx = daily["Revenue"].idxmin()
        else:
            soft_idx = None

        if peak_idx is not None:
            peak_dt = daily.loc[peak_idx, "Day_Date"]
            peak_day = peak_dt.strftime("%b %d, %Y")
            peak_weekday = peak_dt.strftime("%A")
            peak_rev = float(daily.loc[peak_idx, "Revenue"])
        else:
            peak_day, peak_weekday, peak_rev = "N/A", "N/A", 0.0

        if soft_idx is not None and soft_idx != peak_idx:
            soft_dt = daily.loc[soft_idx, "Day_Date"]
            soft_day = soft_dt.strftime("%b %d, %Y")
            soft_rev = float(daily.loc[soft_idx, "Revenue"])
        elif len(daily) > 1:
            other_indices = [i for i in daily.index if i != peak_idx]
            soft_idx = other_indices[0]
            soft_dt = daily.loc[soft_idx, "Day_Date"]
            soft_day = soft_dt.strftime("%b %d, %Y")
            soft_rev = float(daily.loc[soft_idx, "Revenue"])
        else:
            soft_day, soft_rev = "Baseline Run-Rate", peak_rev

        month_name = min_date.strftime("%B %Y") if pd.notna(min_date) else "Period"
        trend_title = f"Daily Performance & Run-Rate ({month_name})"

        insights_out = {
            "time_horizon": "daily",
            "horizon_desc": horizon_info["desc"],
            "trend_title": trend_title,
            "best_period": peak_day,
            "worst_period": soft_day,
            "best_period_tag": "🏆 Peak Day Velocity",
            "worst_period_tag": "⚠️ Softest Day Run-Rate",
            "best_period_desc": f"Highest single-day velocity recorded ({sym}{peak_rev:,.0f}). Velocity surged on {peak_weekday}.",
            "worst_period_desc": f"Lowest recorded daily velocity ({sym}{soft_rev:,.0f}). Represents primary opportunity for pacing.",
            "period_guidance": f"Align daily operational staffing, inventory flow, and ad spend with peak {peak_weekday} velocity.",
            "growth_rate_metric": "DoD",
            "avg_growth_rate": round(daily["MoM_Growth"].dropna().mean(), 2) if not daily["MoM_Growth"].dropna().empty else 0.0,
        }
        return daily, insights_out

    elif horizon == "quarterly":
        # 6 to 24 months: Compute quarterly milestone metrics + continuous monthly series
        df_copy = df.copy()
        df_copy["Quarter"] = df_copy["Date"].dt.to_period("Q")
        quarterly = df_copy.groupby("Quarter").agg(**agg_dict).reset_index()
        quarterly["Quarter_Label"] = quarterly["Quarter"].apply(lambda q: f"Q{q.quarter} {q.year}")
        if not has_profit or "Profit" not in quarterly.columns:
            quarterly["Profit"] = 0.0

        best_q_idx = quarterly["Revenue"].idxmax() if not quarterly.empty else None
        worst_q_idx = quarterly["Revenue"].idxmin() if not quarterly.empty else None

        if best_q_idx is not None and worst_q_idx is not None:
            best_q = quarterly.loc[best_q_idx, "Quarter_Label"]
            worst_q = quarterly.loc[worst_q_idx, "Quarter_Label"]
            best_q_rev = float(quarterly.loc[best_q_idx, "Revenue"])
            worst_q_rev = float(quarterly.loc[worst_q_idx, "Revenue"])
            total_q_rev = float(quarterly["Revenue"].sum())
            best_pct = round((best_q_rev / total_q_rev * 100), 1) if total_q_rev else 0.0
            worst_pct = round((worst_q_rev / total_q_rev * 100), 1) if total_q_rev else 0.0
            if best_q == worst_q and len(quarterly) > 1:
                other_idx = [i for i in quarterly.index if i != best_q_idx]
                worst_q_idx = other_idx[0]
                worst_q = quarterly.loc[worst_q_idx, "Quarter_Label"]
                worst_q_rev = float(quarterly.loc[worst_q_idx, "Revenue"])
                worst_pct = round((worst_q_rev / total_q_rev * 100), 1) if total_q_rev else 0.0
        else:
            best_q, worst_q = "N/A", "N/A"
            best_q_rev, worst_q_rev, best_pct, worst_pct = 0.0, 0.0, 0.0, 0.0

        monthly = monthly_trend(df, has_profit=has_profit)
        trend_title = "Quarterly & Monthly Performance Trajectory"

        insights_out = {
            "time_horizon": "quarterly",
            "horizon_desc": horizon_info["desc"],
            "trend_title": trend_title,
            "best_period": best_q,
            "worst_period": worst_q,
            "best_period_tag": "🏆 Peak Fiscal Quarter",
            "worst_period_tag": "⚠️ Softest Fiscal Quarter",
            "best_period_desc": f"Delivered {best_pct}% of total volume ({sym}{best_q_rev:,.0f}). Strongest quarterly execution.",
            "worst_period_desc": f"Generated {worst_pct}% of volume ({sym}{worst_q_rev:,.0f}). Target for counter-cyclical growth initiatives.",
            "period_guidance": f"Ramp up commercial capacity and marketing budgets 45 days prior to {best_q} to maximize capture rate.",
            "growth_rate_metric": "MoM",
            "avg_growth_rate": round(monthly["MoM_Growth"].dropna().mean(), 2) if not monthly.empty else 0.0,
        }
        return monthly, insights_out

    elif horizon == "annual":
        # > 24 months (Multi-Year)
        df_copy = df.copy()
        df_copy["Year"] = df_copy["Date"].dt.year
        annual = df_copy.groupby("Year").agg(**agg_dict).reset_index()
        if not has_profit or "Profit" not in annual.columns:
            annual["Profit"] = 0.0

        best_y_idx = annual["Revenue"].idxmax() if not annual.empty else None
        worst_y_idx = annual["Revenue"].idxmin() if not annual.empty else None

        if best_y_idx is not None:
            best_y = str(annual.loc[best_y_idx, "Year"])
            best_y_rev = float(annual.loc[best_y_idx, "Revenue"])
        else:
            best_y, best_y_rev = "N/A", 0.0

        if worst_y_idx is not None and worst_y_idx != best_y_idx:
            worst_y = str(annual.loc[worst_y_idx, "Year"])
            worst_y_rev = float(annual.loc[worst_y_idx, "Revenue"])
        elif len(annual) > 1:
            other_idx = [i for i in annual.index if i != best_y_idx]
            worst_y = str(annual.loc[other_idx[0], "Year"])
            worst_y_rev = float(annual.loc[other_idx[0], "Revenue"])
        else:
            worst_y, worst_y_rev = "Base Year", best_y_rev

        monthly = monthly_trend(df, has_profit=has_profit)
        trend_title = "Multi-Year Macro Growth & Trajectory"

        insights_out = {
            "time_horizon": "annual",
            "horizon_desc": horizon_info["desc"],
            "trend_title": trend_title,
            "best_period": f"FY {best_y}",
            "worst_period": f"FY {worst_y}",
            "best_period_tag": "🏆 Peak Fiscal Year",
            "worst_period_tag": "⚠️ Base / Transition Year",
            "best_period_desc": f"Record annual output ({sym}{best_y_rev:,.0f}). Anchor period for multi-year expansion.",
            "worst_period_desc": f"Foundational baseline volume ({sym}{worst_y_rev:,.0f}) before sustained period-over-period acceleration.",
            "period_guidance": f"Apply structural operational leverage proven in FY {best_y} across upcoming budget cycles.",
            "growth_rate_metric": "YoY",
            "avg_growth_rate": round(monthly["MoM_Growth"].dropna().mean(), 2) if not monthly.empty else 0.0,
        }
        return monthly, insights_out

    else:
        # Standard Short Multi-Month (2 to 5 months)
        monthly = monthly_trend(df, has_profit=has_profit)
        best_m = monthly.loc[monthly["Revenue"].idxmax(), "Month_Label"] if not monthly.empty else "N/A"
        worst_m = monthly.loc[monthly["Revenue"].idxmin(), "Month_Label"] if not monthly.empty else "N/A"
        if best_m == worst_m and len(monthly) > 1:
            other_m = [m for m in monthly["Month_Label"] if m != best_m]
            if other_m:
                worst_m = other_m[0]

        trend_title = "Monthly Revenue & Profit Trajectory"
        insights_out = {
            "time_horizon": "monthly",
            "horizon_desc": horizon_info["desc"],
            "trend_title": trend_title,
            "best_period": best_m,
            "worst_period": worst_m,
            "best_period_tag": "🏆 Top Monthly Performance",
            "worst_period_tag": "⚠️ Contraction Window",
            "best_period_desc": "Highest activity concentration recorded across the multi-month period.",
            "worst_period_desc": "Softest period recorded. Primary opportunity for strategic counter-cyclical initiatives.",
            "period_guidance": f"Rebalance promotional calendar and inventory allocation heading into {worst_m}.",
            "growth_rate_metric": "MoM",
            "avg_growth_rate": round(monthly["MoM_Growth"].dropna().mean(), 2) if not monthly.empty else 0.0,
        }
        return monthly, insights_out


def monthly_trend(df: pd.DataFrame, has_profit: bool = True) -> pd.DataFrame:
    df["Month"] = df["Date"].dt.to_period("M")
    agg_dict = {"Revenue": ("Revenue", "sum"), "Orders": ("Revenue", "count")}
    if has_profit and "Profit" in df.columns:
        agg_dict["Profit"] = ("Profit", "sum")

    monthly = df.groupby("Month").agg(**agg_dict).reset_index()
    if not has_profit or "Profit" not in monthly.columns:
        monthly["Profit"] = 0.0

    # Continuous monthly reindexing: Ensure every intermediate month exists
    if not monthly.empty:
        full_idx = pd.period_range(start=monthly["Month"].min(), end=monthly["Month"].max(), freq="M")
        monthly = monthly.set_index("Month").reindex(full_idx, fill_value=0.0).reset_index()
        monthly.rename(columns={"index": "Month"}, inplace=True)
        if "Orders" in monthly.columns:
            monthly["Orders"] = monthly["Orders"].fillna(0).astype(int)

    monthly["Month_Label"] = monthly["Month"].dt.strftime("%b %Y")
    monthly["MoM_Growth"]  = monthly["Revenue"].pct_change() * 100

    # Partial first/last month detection
    min_date = df["Date"].min()
    max_date = df["Date"].max()
    monthly["Is_Partial"] = False
    if not monthly.empty and pd.notna(min_date) and pd.notna(max_date):
        if min_date.day > 10:
            monthly.loc[monthly.index[0], "Is_Partial"] = True
        days_in_last = pd.Period(max_date, freq="D").days_in_month
        if max_date.day < (days_in_last - 5):
            monthly.loc[monthly.index[-1], "Is_Partial"] = True

    return monthly


def detect_time_series_anomalies(monthly: pd.DataFrame, z_threshold: float = 2.0, mom_threshold: float = 40.0, currency_symbol: str = "$") -> list:
    """
    Robust statistical anomaly detection on time-series monthly revenue using Median
    and Median Absolute Deviation (MAD) to prevent normal fluctuations from triggering alerts.
    Identifies significant surges and contractions with partial-month awareness.
    """
    if monthly is None or len(monthly) < 3 or "Revenue" not in monthly.columns:
        return []

    rev = monthly["Revenue"]
    rev_median = float(rev.median())
    abs_diffs = (rev - rev_median).abs()
    mad = float(abs_diffs.median())

    # Normalization factor for MAD to approximate standard deviation
    norm_factor = 1.4826 if mad > 0 else 1.0
    scale = mad * norm_factor if mad > 0 else float(rev.std())

    if scale == 0 or pd.isna(scale):
        return []

    anomalies = []
    for _, row in monthly.iterrows():
        r_val = float(row["Revenue"])
        z_robust = (r_val - rev_median) / scale
        mom = float(row["MoM_Growth"]) if "MoM_Growth" in row and pd.notna(row["MoM_Growth"]) else 0.0
        pct_diff = ((r_val - rev_median) / rev_median * 100.0) if rev_median != 0 else 0.0
        is_partial = bool(row.get("Is_Partial", False))

        is_spike = (z_robust >= z_threshold) or (mom >= mom_threshold and z_robust >= 1.5)
        is_drop  = (z_robust <= -z_threshold) or (mom <= -mom_threshold and z_robust <= -1.5)

        if is_spike or is_drop:
            anom_type = "Surge" if is_spike else "Contraction"
            partial_note = " (Partial month)" if is_partial else ""
            anomalies.append({
                "period": str(row.get("Month_Label", str(row.get("Month", "Unknown")))),
                "type": anom_type,
                "metric": "Revenue",
                "value": round(r_val, 2),
                "z_score": round(float(z_robust), 2),
                "pct_diff_mean": round(float(pct_diff), 1),
                "mom_growth": round(float(mom), 1),
                "is_partial": is_partial,
                "severity": "High" if abs(z_robust) >= 3.0 else "Moderate",
                "summary": f"{row.get('Month_Label', 'Month')}: {anom_type} of {currency_symbol}{r_val:,.0f} ({z_robust:+.2f}σ vs. median, {pct_diff:+.1f}%){partial_note}",
            })

    return sorted(anomalies, key=lambda a: abs(a["z_score"]), reverse=True)


def category_breakdown(df: pd.DataFrame, has_profit: bool = True, max_categories: int = 12) -> pd.DataFrame:
    agg_dict = {"Revenue": ("Revenue", "sum"), "Orders": ("Revenue", "count")}
    if has_profit and "Profit" in df.columns:
        agg_dict["Profit"] = ("Profit", "sum")

    cat = df.groupby("Category").agg(**agg_dict).reset_index()
    if not has_profit or "Profit" not in cat.columns:
        cat["Profit"] = 0.0

    # High-cardinality guard: if more than 12 unique categories, keep top 10 and roll the rest into "Other"
    if len(cat) > max_categories:
        cat = cat.sort_values("Revenue", ascending=False)
        top_slice = cat.iloc[:10].copy()
        other_slice = cat.iloc[10:]

        other_rev = float(other_slice["Revenue"].sum())
        other_orders = int(other_slice["Orders"].sum())
        other_profit = float(other_slice["Profit"].sum()) if "Profit" in other_slice.columns else 0.0

        other_row = pd.DataFrame([{
            "Category": f"Other ({len(other_slice)} items)",
            "Revenue": other_rev,
            "Orders": other_orders,
            "Profit": other_profit,
        }])
        cat = pd.concat([top_slice, other_row], ignore_index=True)
    else:
        cat = cat.sort_values("Revenue", ascending=False)

    if has_profit and "Profit" in cat.columns:
        cat["Margin_%"] = (cat["Profit"] / cat["Revenue"].replace(0, np.nan) * 100).fillna(0.0).round(2)
    else:
        cat["Margin_%"] = 0.0

    total_rev = cat["Revenue"].sum()
    cat["Revenue_%"] = (cat["Revenue"] / total_rev * 100).round(2) if total_rev else 0.0
    return cat


def region_breakdown(df: pd.DataFrame, max_regions: int = 12) -> pd.DataFrame:
    reg = (
        df.groupby("Region")
          .agg(Revenue=("Revenue", "sum"))
          .reset_index()
    )
    # High-cardinality guard: if more than 12 unique regions, keep top 10 and roll the rest into "Other"
    if len(reg) > max_regions:
        reg = reg.sort_values("Revenue", ascending=False)
        top_slice = reg.iloc[:10].copy()
        other_slice = reg.iloc[10:]
        other_rev = float(other_slice["Revenue"].sum())
        other_row = pd.DataFrame([{
            "Region": f"Other ({len(other_slice)} regions)",
            "Revenue": other_rev,
        }])
        reg = pd.concat([top_slice, other_row], ignore_index=True)
    else:
        reg = reg.sort_values("Revenue", ascending=False)

    total_rev = reg["Revenue"].sum()
    reg["Revenue_%"] = (reg["Revenue"] / total_rev * 100).round(2) if total_rev else 0.0
    return reg


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


def build_report_from_df(df: pd.DataFrame, mapping: dict = None, report_mode: str = "Sales & Retail Performance", currency_symbol: str = "$", **kwargs) -> dict:
    """
    Core deterministic data engine. Takes any raw or mapped DataFrame,
    normalizes columns, strips currency characters, deduplicates, filters summary rows,
    and computes all KPIs. Single Source of Truth for both the Web UI and PowerPoint Generator.
    """
    clean_df = df.copy()

    raw_row_count = len(df)
    symbols_cleaned_total = 0
    nulls_imputed_total = 0
    audit_trail = []
    quarantine_records = []

    # 1. Clean column headers and drop empty Unnamed columns
    clean_df.columns = [re.sub(r'\s+', ' ', str(c)).strip() for c in clean_df.columns]
    unnamed_cols = [c for c in clean_df.columns if str(c).lower().startswith("unnamed:") and clean_df[c].isna().all()]
    if unnamed_cols:
        clean_df = clean_df.drop(columns=unnamed_cols)
        audit_trail.append(f"Dropped {len(unnamed_cols)} empty trailing column(s)")

    # 2. Filter out completely blank rows
    empty_mask = clean_df.isna().all(axis=1)
    if empty_mask.any():
        empty_cnt = int(empty_mask.sum())
        empty_rows = clean_df[empty_mask].copy()
        empty_rows["quarantine_reason"] = "Completely blank row"
        quarantine_records.append(empty_rows)
        clean_df = clean_df[~empty_mask].copy()
        audit_trail.append(f"Dropped {empty_cnt} completely blank row(s)")

    # 3. Filter out 'Total', 'Grand Total', 'Subtotal' summary rows
    summary_keywords = {"total", "grand total", "subtotal", "sub total", "totals", "summary", "sum"}
    is_summary_row = pd.Series(False, index=clean_df.index)
    for col in clean_df.columns:
        if not pd.api.types.is_numeric_dtype(clean_df[col]):
            matches = clean_df[col].astype(str).str.strip().str.lower().isin(summary_keywords)
            is_summary_row = is_summary_row | matches

    if is_summary_row.any():
        summary_count = int(is_summary_row.sum())
        summary_rows = clean_df[is_summary_row].copy()
        summary_rows["quarantine_reason"] = "Summary / Total row (prevented metric double-counting)"
        quarantine_records.append(summary_rows)
        clean_df = clean_df[~is_summary_row].copy()
        audit_trail.append(f"Excluded {summary_count} summary row(s) ('Total'/'Grand Total' to prevent double-counting)")
    else:
        summary_count = 0

    # 4. Remove exact duplicate rows
    dup_mask = clean_df.duplicated(keep="first")
    if dup_mask.any():
        dup_count = int(dup_mask.sum())
        dup_rows = clean_df[dup_mask].copy()
        dup_rows["quarantine_reason"] = "Exact duplicate row"
        quarantine_records.append(dup_rows)
        clean_df = clean_df[~dup_mask].copy()
        audit_trail.append(f"Deduplicated {dup_count} exact redundant row(s)")
    else:
        dup_count = 0

    has_mapped_profit = ("Profit" in df.columns) if not mapping else False
    has_mapped_cost   = ("Cost" in df.columns) if not mapping else False

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

    # Standardize Date column with mixed-format and numeric Excel serial resilience
    if "Date" in clean_df.columns:
        if pd.api.types.is_numeric_dtype(clean_df["Date"]):
            try:
                parsed_dates = pd.to_datetime(clean_df["Date"], unit="D", origin="1899-12-30")
            except Exception:
                parsed_dates = pd.to_datetime(clean_df["Date"], errors="coerce")
        else:
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

    # 5. Normalize text columns across the entire dataset (strip leading/trailing spaces and collapse internal double spaces)
    key_categories = {"category", "region", "product", "channel", "department", "cost_center"}
    for col in clean_df.columns:
        if not pd.api.types.is_numeric_dtype(clean_df[col]) and not pd.api.types.is_datetime64_any_dtype(clean_df[col]):
            should_title = str(col).lower() in key_categories
            clean_df[col] = normalize_text_series(clean_df[col], to_title_case=should_title)

    if "Category" not in clean_df.columns:
        clean_df["Category"] = "All Categories"

    if "Region" not in clean_df.columns:
        clean_df["Region"] = "All Regions"

    if "Product" not in clean_df.columns:
        clean_df["Product"] = clean_df["Category"]

    audit_trail.append("Sanitized text fields (trimmed whitespace, collapsed double spaces & applied Title Case)")

    # 6. Assemble quarantined rows dataset
    if quarantine_records:
        quarantined_df = pd.concat(quarantine_records, ignore_index=True)
    else:
        quarantined_df = pd.DataFrame(columns=list(clean_df.columns) + ["quarantine_reason"])

    total_modifications = symbols_cleaned_total + nulls_imputed_total + dropped_rows_total + dup_count + summary_count
    if total_modifications == 0:
        health_score = 100
        health_status = "Certified Clean"
    elif nulls_imputed_total == 0 and dropped_rows_total == 0 and dup_count == 0 and summary_count == 0:
        health_score = 99
        health_status = f"High Integrity ({symbols_cleaned_total} formatted symbols sanitized)"
    else:
        penalty = min(25, (nulls_imputed_total * 2) + (dropped_rows_total * 4) + (dup_count * 2) + (summary_count * 3))
        health_score = max(70, 100 - penalty)
        health_status = f"Sanitized ({total_modifications} modifications)"

    hygiene = {
        "raw_row_count": raw_row_count,
        "clean_row_count": clean_row_count,
        "dropped_rows_count": dropped_rows_total,
        "rows_retained_pct": retention_pct,
        "currency_symbols_stripped": symbols_cleaned_total,
        "missing_values_imputed": nulls_imputed_total,
        "duplicates_removed": dup_count,
        "summary_rows_removed": summary_count,
        "quarantined_rows_count": len(quarantined_df),
        "date_range": date_range_str,
        "health_score": health_score,
        "health_status": health_status,
        "audit_log": audit_trail,
    }

    kpis     = compute_kpis(clean_df, has_profit=has_profit, report_mode=report_mode)
    horizon_info = detect_time_horizon(clean_df)
    monthly, time_insights = compute_adaptive_time_series(clean_df, horizon_info, has_profit=has_profit, currency_symbol=currency_symbol)
    category = category_breakdown(clean_df, has_profit=has_profit)
    region   = region_breakdown(clean_df)
    products = top_products(clean_df, n=10)

    has_channel = ("Channel" in clean_df.columns) and (clean_df["Channel"].nunique() > 1 or clean_df["Channel"].iloc[0] != "Direct")
    channels = channel_breakdown(clean_df) if has_channel else pd.DataFrame({
        "Channel": ["Direct"], "Revenue": [kpis["total_revenue"]], "Orders": [kpis["total_orders"]], "Revenue_%": [100.0]
    })

    best_period  = time_insights.get("best_period", "N/A")
    worst_period = time_insights.get("worst_period", "N/A")
    best_month   = best_period
    worst_month  = worst_period
    avg_mom_growth = monthly["MoM_Growth"].dropna().mean() if not monthly.empty else 0.0

    # CMGR (Compound Monthly Growth Rate) computation
    n_months = len(monthly)
    if n_months >= 2:
        rev_start = float(monthly.iloc[0]["Revenue"])
        rev_end = float(monthly.iloc[-1]["Revenue"])
        if rev_start > 0 and rev_end > 0:
            cmgr = ((rev_end / rev_start) ** (1.0 / (n_months - 1)) - 1.0) * 100.0
        else:
            cmgr = float(monthly["MoM_Growth"].dropna().median()) if "MoM_Growth" in monthly and not monthly["MoM_Growth"].dropna().empty else 0.0
    else:
        cmgr = 0.0

    growth_arrow = "↑" if cmgr >= 0 else "↓"
    growth_sign = "+" if cmgr >= 0 else ""
    growth_label = f"{growth_arrow} {growth_sign}{cmgr:.1f}% CMGR"

    partial_months = monthly[monthly["Is_Partial"]]["Month_Label"].tolist() if "Is_Partial" in monthly else []

    top_cat     = category.iloc[0]["Category"] if not category.empty else "General"
    top_region  = region.iloc[0]["Region"] if not region.empty else "Global"
    top_channel = channels.iloc[0]["Channel"] if has_channel and not channels.empty else None

    anomalies = detect_time_series_anomalies(monthly, currency_symbol=currency_symbol)
    has_anomalies = len(anomalies) > 0
    if has_anomalies:
        top_anom = anomalies[0]
        anomaly_headline = f"{top_anom['period']} experienced a statistical {top_anom['type'].lower()} ({top_anom['z_score']:+.2f}σ vs. median, {top_anom['pct_diff_mean']:+.1f}%)."
    else:
        anomaly_headline = "Trajectory remained within expected historical bounds with no abnormal volatility."

    meta_dict = get_mode_kpi_labels(report_mode)
    meta_dict["currency_symbol"] = currency_symbol
    meta_dict["trend_title"] = time_insights.get("trend_title", meta_dict.get("trend_title", "Performance Trajectory"))
    meta_dict["time_horizon"] = horizon_info["horizon"]
    meta_dict["horizon_desc"] = horizon_info["desc"]

    return {
        "df":             clean_df,
        "quarantined_df": quarantined_df,
        "kpis":           kpis,
        "monthly":        monthly,
        "category":       category,
        "region":         region,
        "top_products":   products,
        "channels":       channels,
        "report_mode":  report_mode,
        "meta":         meta_dict,
        "insights": {
            "best_month":        best_month,
            "worst_month":       worst_month,
            "best_period":       best_period,
            "worst_period":      worst_period,
            "best_period_tag":   time_insights.get("best_period_tag", "🏆 Peak Performance Period"),
            "worst_period_tag":  time_insights.get("worst_period_tag", "⚠️ Contraction Window"),
            "best_period_desc":  time_insights.get("best_period_desc", "Highest activity concentration recorded."),
            "worst_period_desc": time_insights.get("worst_period_desc", "Softest period recorded. Primary opportunity for strategic initiatives."),
            "period_guidance":   time_insights.get("period_guidance", f"Ramp up operational readiness 45 days prior to {best_period} to maximize capture rate."),
            "trend_title":       time_insights.get("trend_title", "Performance Trajectory"),
            "time_horizon":      horizon_info["horizon"],
            "horizon_desc":      horizon_info["desc"],
            "avg_mom_growth":    round(avg_mom_growth, 2) if not pd.isna(avg_mom_growth) else 0.0,
            "cmgr":              round(cmgr, 2),
            "growth_arrow":      growth_arrow,
            "growth_label":      growth_label,
            "partial_months":    partial_months,
            "top_category":      top_cat,
            "top_region":        top_region,
            "top_channel":       top_channel,
            "has_channel":       has_channel,
            "anomalies":         anomalies,
            "has_anomalies":     has_anomalies,
            "anomaly_headline":  anomaly_headline,
        },
        "hygiene": hygiene,
    }


def build_report(filepath: str, report_mode: str = "Sales & Retail Performance", currency_symbol: str = "$", **kwargs) -> dict:
    df = load_and_validate(filepath)
    return build_report_from_df(df, report_mode=report_mode, currency_symbol=currency_symbol, **kwargs)


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

"""
analysis_engine.py
Ingests the sales CSV and computes all KPIs, trends, and rankings.
Returns a clean 'report_data' dictionary used by the chart and slide generators.
"""

import pandas as pd
import numpy as np
import re
import datetime


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

    # Check suffixes: K, M, B, T (case-insensitive)
    multiplier = 1.0
    match_suffix = re.search(r'([0-9.,]+)\s*([kKmMbBtT])\b', s)
    if match_suffix:
        num_part = match_suffix.group(1)
        suffix = match_suffix.group(2).upper()
        if suffix == 'K':
            multiplier = 1e3
        elif suffix == 'M':
            multiplier = 1e6
        elif suffix == 'B':
            multiplier = 1e9
        elif suffix == 'T':
            multiplier = 1e12
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
        try:
            float(original)
            was_formatted = False   # already a plain number stored as text
        except ValueError:
            was_formatted = True
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


def sanitize_numeric_with_mask(series: pd.Series) -> tuple:
    """Like sanitize_numeric_column, but unparseable/missing values stay NaN so the caller can
    quarantine those rows instead of silently turning them into 0.
    Returns (float_series_with_NaN, formatted_count, invalid_mask)."""
    if pd.api.types.is_numeric_dtype(series):
        out = pd.to_numeric(series, errors="coerce").astype(float)
        return out, 0, out.isna()
    parsed = [parse_single_numeric(v) for v in series]
    invalid = pd.Series([p[1] for p in parsed], index=series.index)
    vals = pd.Series([np.nan if p[1] else p[0] for p in parsed], index=series.index, dtype=float)
    fmt_cnt = int(sum(1 for p in parsed if p[2]))
    return vals, fmt_cnt, invalid


def consolidate_case_variants(series: pd.Series) -> tuple:
    """Merge spellings that differ only by case/whitespace ('north', 'NORTH' -> most common form).
    Never changes capitalization of values that have no variants (so 'USB-C Hub' stays as is).
    Returns (series, number_of_values_changed)."""
    mask = series.notna()
    if not mask.any():
        return series, 0
    vals = series[mask].astype(str)
    key = vals.str.lower()
    canon = vals.groupby(key).agg(lambda g: g.value_counts().idxmax())
    new_vals = key.map(canon)
    changed = int((new_vals != vals).sum())
    out = series.copy()
    out.loc[mask] = new_vals
    return out, changed


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
    """Read any CSV/Excel file as-is. Column detection and cleaning happen in build_report_from_df
    (which uses infer_mapping), so files do not need exact 'Date'/'Revenue' headers."""
    from io_utils import read_tabular_path
    df, _notes = read_tabular_path(filepath)
    if df.empty:
        raise ValueError("The file contains no rows.")
    return df


def compute_kpis(df: pd.DataFrame, has_profit: bool = True, report_mode: str = "Sales & Retail Performance") -> dict:
    mode = report_mode or "Sales & Retail Performance"
    has_units = "Quantity" in df.columns
    has_returns = "Returned" in df.columns
    total_orders = len(df)
    total_units = int(df["Quantity"].sum(skipna=True)) if has_units else total_orders
    units_coverage_pct = round(float(df["Quantity"].notna().mean() * 100), 1) if has_units and total_orders else 100.0
    profit_coverage_pct = round(float(df["Profit"].notna().mean() * 100), 1) if (has_profit and "Profit" in df.columns and total_orders) else 100.0
    cov_note = f" · from {profit_coverage_pct:.0f}% of rows" if profit_coverage_pct < 100.0 else ""
    return_rate = round((df["Returned"].sum() / total_orders * 100), 2) if has_returns and total_orders else 0.0

    if "Marketing" in mode:
        # Spend = Revenue column. Conversions and Return are separate, explicit columns.
        total_spend = float(df["Revenue"].sum())
        has_conv = "Conversions" in df.columns
        conversions = float(df["Conversions"].sum(skipna=True)) if has_conv else None
        has_return = bool(has_profit and "Profit" in df.columns)
        total_return = float(df["Profit"].sum(skipna=True)) if has_return else None
        # like-for-like: only rows where BOTH sides of the ratio exist
        if has_conv:
            spend_m = float(df.loc[df["Conversions"].notna(), "Revenue"].sum())
            cpa = round(spend_m / conversions, 2) if (conversions and conversions > 0) else None
        else:
            cpa = None
        if has_return:
            m_ = df["Profit"].notna()
            spend_r = float(df.loc[m_, "Revenue"].sum())
            roas = round(float(df.loc[m_, "Profit"].sum()) / spend_r, 2) if spend_r > 0 else None
        else:
            roas = None

        if roas is not None:
            eff_name, eff_display = "ROAS", f"{roas:.2f}x"
            eff_status = ("Target: >2.0x" if roas >= 2.0 else "Below 2.0x Target") + cov_note
            eff_class = "pill-purple" if roas >= 2.0 else "pill-amber"
        else:
            eff_name, eff_display = "ROAS", "N/A"
            eff_status = "Map a Return Value column to compute ROAS"
            eff_class = "pill-blue"

        return {
            "total_revenue": round(total_spend, 2),
            "total_profit": round(total_return, 2) if total_return is not None else None,
            "total_cost": round(total_spend, 2),
            "total_orders": int(conversions) if conversions is not None else 0,
            "total_units": int(conversions) if conversions is not None else 0,
            "has_units": False,
            "has_returns": False,
            "has_conversions": has_conv,
            "avg_order_value": cpa,
            "profit_margin": roas,
            "return_rate": 0.0,
            "has_profit": has_return,
            "efficiency_metric_name": eff_name,
            "efficiency_display": eff_display,
            "efficiency_status": eff_status,
            "efficiency_pill_class": eff_class,
            "roas": roas,
            "cpa": cpa,
            "profit_coverage_pct": profit_coverage_pct,
            "units_coverage_pct": units_coverage_pct,
            "conversions_coverage_pct": round(float(df["Conversions"].notna().mean() * 100), 1) if has_conv and total_orders else 100.0,
        }

    elif "Operations" in mode:
        # Budget = Revenue column; Actual = Profit column (mapped from "Actual Expenses").
        budget = float(df["Revenue"].sum())
        has_actual = bool(has_profit and "Profit" in df.columns)
        if has_actual:
            m_ = df["Profit"].notna()
            actual = float(df.loc[m_, "Profit"].sum())
            budget_m = float(df.loc[m_, "Revenue"].sum())      # budget for the same rows as the actuals
            n_actual = int(m_.sum())
        else:
            actual = None
        if actual is not None:
            variance = round(actual - budget_m, 2)  # positive = overspend, like-for-like rows
            utilization_pct = round(actual / budget_m * 100, 1) if budget_m > 0 else None
            cost_per_item = round(actual / n_actual, 2) if n_actual > 0 else None
        else:
            variance = utilization_pct = cost_per_item = None

        eff_name = "Budget Utilization"
        if utilization_pct is None:
            eff_display, eff_status, eff_class = "N/A", "Map an Actual Expenses column", "pill-blue"
        else:
            eff_display = f"{utilization_pct:.1f}%"
            if utilization_pct > 100.0:
                eff_status = f"Over Budget by {abs(variance):,.0f}"
                eff_class = "pill-red"
            elif utilization_pct >= 90.0:
                eff_status = f"Near Limit ({abs(variance):,.0f} remaining)"
                eff_class = "pill-amber"
            else:
                eff_status = f"On Budget ({abs(variance):,.0f} remaining)"
                eff_class = "pill-green"

        return {
            "total_revenue": round(budget, 2),
            "total_profit": round(actual, 2) if actual is not None else None,
            "total_cost": round(actual, 2) if actual is not None else None,
            "total_orders": total_orders,
            "total_units": total_units,
            "has_units": has_units,
            "has_returns": has_returns,
            "avg_order_value": cost_per_item,
            "profit_margin": utilization_pct,
            "return_rate": return_rate,
            "has_profit": has_actual,
            "efficiency_metric_name": eff_name,
            "efficiency_display": eff_display,
            "efficiency_status": eff_status,
            "efficiency_pill_class": eff_class,
            "budget_variance": variance,
            "budget_utilization": utilization_pct,
            "profit_coverage_pct": profit_coverage_pct,
            "units_coverage_pct": units_coverage_pct,
        }

    else:
        # Sales & Retail Performance
        total_revenue = float(df["Revenue"].sum())
        avg_order_val = round((total_revenue / total_orders), 2) if total_orders else 0.0

        if has_profit and "Profit" in df.columns:
            m_ = df["Profit"].notna()
            total_profit = float(df.loc[m_, "Profit"].sum())
            total_cost = float(df["Cost"].sum(skipna=True)) if "Cost" in df.columns else 0.0
            rev_matched = float(df.loc[m_, "Revenue"].sum())      # margin only over rows that HAVE a profit figure
            profit_margin = round((total_profit / rev_matched * 100), 2) if rev_matched else 0.0
            eff_display = f"{profit_margin:.1f}%"
            eff_status = ("Target: >35.0%" if profit_margin >= 35.0 else "Below 35% Target") + cov_note
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
            "profit_coverage_pct": profit_coverage_pct,
            "units_coverage_pct": units_coverage_pct,
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


def get_available_time_scopes(df: pd.DataFrame) -> dict:
    """
    Returns detected years, span, and recommended granularities for interactive drilldowns.
    """
    if df is None or "Date" not in df.columns or df["Date"].dropna().empty:
        curr_y = datetime.date.today().year
        return {
            "years": [curr_y],
            "is_multi_year": False,
            "default_year": curr_y,
            "granularities": ["Monthly", "Quarterly", "Daily"],
            "unique_months": 12,
            "span_days": 365,
        }

    valid_dates = pd.to_datetime(df["Date"].dropna(), errors="coerce").dropna()
    if valid_dates.empty:
        curr_y = datetime.date.today().year
        return {
            "years": [curr_y],
            "is_multi_year": False,
            "default_year": curr_y,
            "granularities": ["Monthly", "Quarterly", "Daily"],
            "unique_months": 12,
            "span_days": 365,
        }

    years = sorted([int(y) for y in valid_dates.dt.year.unique()])
    is_multi_year = len(years) > 1
    span_days = max(1, (valid_dates.max() - valid_dates.min()).days)
    unique_months = valid_dates.dt.to_period("M").nunique()

    if is_multi_year:
        granularities = ["Yearly", "Quarterly", "Monthly", "Weekly", "Daily"]
    elif span_days <= 45 or unique_months <= 1:
        granularities = ["Weekly", "Daily"]
    else:
        granularities = ["Quarterly", "Monthly", "Weekly", "Daily"]

    return {
        "years": years,
        "is_multi_year": is_multi_year,
        "default_year": years[-1] if years else datetime.date.today().year,
        "granularities": granularities,
        "unique_months": unique_months,
        "span_days": span_days,
        "scope_options": get_time_scope_options(df),
    }


def get_time_scope_options(df: pd.DataFrame) -> list[dict]:
    """
    Builds a list of intuitive executive time scopes (Full Timeline, Specific Years, Quarters, Months)
    available in the dataset.
    """
    if df is None or "Date" not in df.columns or df["Date"].dropna().empty:
        return [{"id": "all", "label": "Full Dataset"}]

    valid_dates = pd.to_datetime(df["Date"].dropna(), errors="coerce").dropna()
    if valid_dates.empty:
        return [{"id": "all", "label": "Full Dataset"}]

    years = sorted([int(y) for y in valid_dates.dt.year.unique()])
    is_multi_year = len(years) > 1
    options = []

    if is_multi_year:
        options.append({"id": "all", "label": f"Full Timeline ({years[0]} - {years[-1]})"})
        for y in reversed(years):
            options.append({"id": f"year_{y}", "label": f"FY {y} (Full Year)"})
        quarters = sorted(valid_dates.dt.to_period("Q").unique())
        for q in reversed(quarters):
            options.append({"id": f"q_{q}", "label": f"Q{q.quarter} {q.year}"})
    else:
        y = years[0]
        options.append({"id": "all", "label": f"Full Year ({y})"})
        quarters = sorted(valid_dates.dt.to_period("Q").unique())
        if len(quarters) > 1:
            q_names = {1: "Jan - Mar", 2: "Apr - Jun", 3: "Jul - Sep", 4: "Oct - Dec"}
            for q in quarters:
                name_range = q_names.get(q.quarter, "")
                options.append({"id": f"q_{q}", "label": f"Q{q.quarter} {y} ({name_range})"})

        months = sorted(valid_dates.dt.to_period("M").unique())
        if len(months) > 1 and len(months) <= 12:
            for m in months:
                options.append({"id": f"m_{m}", "label": m.strftime("%B %Y")})

    return options


def filter_df_by_time_scope(df: pd.DataFrame, scope_id: str) -> tuple[pd.DataFrame, str]:
    """
    Filters a DataFrame by a chosen scope_id ('all', 'year_2024', 'q_2024Q1', 'm_2024-05').
    Returns (filtered_df, scope_label).
    """
    if df is None or df.empty or "Date" not in df.columns or not scope_id or scope_id == "all":
        return df, "Full Period"

    df_copy = df.copy()
    valid_dates = pd.to_datetime(df_copy["Date"], errors="coerce")

    if scope_id.startswith("year_"):
        y = int(scope_id.split("_")[1])
        mask = valid_dates.dt.year == y
        return df_copy[mask].copy(), f"FY {y}"

    elif scope_id.startswith("q_"):
        q_str = scope_id.split("_", 1)[1]
        try:
            target_q = pd.Period(q_str, freq="Q")
            mask = valid_dates.dt.to_period("Q") == target_q
            return df_copy[mask].copy(), f"Q{target_q.quarter} {target_q.year}"
        except Exception:
            return df_copy, "Full Period"

    elif scope_id.startswith("m_"):
        m_str = scope_id.split("_", 1)[1]
        try:
            target_m = pd.Period(m_str, freq="M")
            mask = valid_dates.dt.to_period("M") == target_m
            return df_copy[mask].copy(), target_m.strftime("%B %Y")
        except Exception:
            return df_copy, "Full Period"

    return df_copy, "Full Period"


def compute_adaptive_time_series(df: pd.DataFrame, horizon_info: dict = None, target_year=None,
                                granularity: str = "auto", has_profit: bool = True,
                                currency_symbol: str = "$") -> tuple[pd.DataFrame, dict]:
    """
    Computes time-series data and insight metadata adapted to the detected time horizon or user drilldown scope.
    Guarantees no redundant comparisons (e.g. single-month files comparing Jan to Jan) and eliminates
    repetitive year suffixes in labels when viewing a single year.
    """
    sym = currency_symbol or "$"

    # 1. Filter by target_year if specified
    if target_year is not None and str(target_year).strip().lower() not in ("all", "all years", "all years (macro)", "none", ""):
        try:
            y_int = int(target_year)
            df_active = df[df["Date"].dt.year == y_int].copy()
            if df_active.empty:
                df_active = df.copy()
                target_year = None
            else:
                target_year = y_int
        except Exception:
            df_active = df.copy()
            target_year = None
    else:
        df_active = df.copy()
        target_year = None

    if horizon_info is None:
        horizon_info = detect_time_horizon(df_active)

    min_date = df_active["Date"].min() if not df_active.empty else horizon_info.get("min_date")
    max_date = df_active["Date"].max() if not df_active.empty else horizon_info.get("max_date")

    agg_dict = {"Revenue": ("Revenue", "sum"), "Orders": ("Revenue", "count")}
    if has_profit and "Profit" in df_active.columns:
        agg_dict["Profit"] = ("Profit", "sum")

    # 2. Resolve active granularity
    if granularity == "auto":
        active_granularity = horizon_info["horizon"]
    else:
        g_map = {"yearly": "annual", "annual": "annual", "quarterly": "quarterly", "monthly": "monthly", "weekly": "weekly", "daily": "daily"}
        active_granularity = g_map.get(str(granularity).lower(), "monthly")

    # Check if this active slice represents a single calendar year
    num_years_in_slice = df_active["Date"].dt.year.nunique() if ("Date" in df_active.columns and not df_active["Date"].dropna().empty) else 1
    is_single_year_slice = (target_year is not None) or (num_years_in_slice <= 1)
    slice_year = target_year or (int(df_active["Date"].dt.year.mode()[0]) if num_years_in_slice >= 1 else datetime.date.today().year)

    # ─────────────────────────────────────────────────────────────────────────────
    # CASE A: DAILY DRILLDOWN
    # ─────────────────────────────────────────────────────────────────────────────
    if active_granularity == "daily":
        df_copy = df_active.copy()
        df_copy["Day_Date"] = df_copy["Date"].dt.floor("D")
        daily = df_copy.groupby("Day_Date").agg(**agg_dict).reset_index()
        if not has_profit or "Profit" not in daily.columns:
            daily["Profit"] = 0.0

        if not daily.empty and pd.notna(min_date) and pd.notna(max_date):
            full_idx = pd.date_range(start=min_date.floor("D"), end=max_date.floor("D"), freq="D")
            daily = daily.set_index("Day_Date").reindex(full_idx, fill_value=0.0).reset_index()
            daily = daily.rename(columns={"index": "Day_Date"})
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

        month_name = min_date.strftime("%B %Y") if pd.notna(min_date) else f"FY {slice_year}"
        trend_title = f"Daily Performance & Run-Rate ({month_name})"

        insights_out = {
            "time_horizon": "daily",
            "granularity": "daily",
            "target_year": target_year,
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
            "x_tick_angle": 0,
        }
        return daily, insights_out

    # ─────────────────────────────────────────────────────────────────────────────
    # CASE B: QUARTERLY DRILLDOWN
    # ─────────────────────────────────────────────────────────────────────────────
    elif active_granularity == "quarterly":
        df_copy = df_active.copy()
        df_copy["Quarter"] = df_copy["Date"].dt.to_period("Q")
        quarterly = df_copy.groupby("Quarter").agg(**agg_dict).reset_index()
        if not has_profit or "Profit" not in quarterly.columns:
            quarterly["Profit"] = 0.0

        if is_single_year_slice:
            # Single year: clean Q1, Q2, Q3, Q4 with no repetitive year suffix!
            quarterly["Quarter_Label"] = quarterly["Quarter"].apply(lambda q: f"Q{q.quarter}")
            trend_title = f"Quarterly Performance Trajectory ({slice_year})"
        else:
            # Multi-year: compact Q1 '24, Q2 '24
            quarterly["Quarter_Label"] = quarterly["Quarter"].apply(lambda q: f"Q{q.quarter} '{str(q.year)[-2:]}")
            min_y = df_active["Date"].dt.year.min()
            max_y = df_active["Date"].dt.year.max()
            trend_title = f"Quarterly Trajectory ({min_y} - {max_y})"

        quarterly["Month_Label"] = quarterly["Quarter_Label"]
        quarterly["Period_Label"] = quarterly["Quarter_Label"]
        quarterly["MoM_Growth"] = quarterly["Revenue"].pct_change() * 100
        quarterly["Is_Partial"] = False

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

        insights_out = {
            "time_horizon": "quarterly",
            "granularity": "quarterly",
            "target_year": target_year,
            "horizon_desc": horizon_info["desc"],
            "trend_title": trend_title,
            "best_period": f"{best_q} {slice_year}" if is_single_year_slice and not best_q.endswith(str(slice_year)) else best_q,
            "worst_period": f"{worst_q} {slice_year}" if is_single_year_slice and not worst_q.endswith(str(slice_year)) else worst_q,
            "best_period_tag": "🏆 Peak Fiscal Quarter",
            "worst_period_tag": "⚠️ Softest Fiscal Quarter",
            "best_period_desc": f"Delivered {best_pct}% of total volume ({sym}{best_q_rev:,.0f}). Strongest quarterly execution.",
            "worst_period_desc": f"Generated {worst_pct}% of volume ({sym}{worst_q_rev:,.0f}). Target for counter-cyclical growth initiatives.",
            "period_guidance": f"Review capacity and planning ahead of best_q, the strongest period in this data.",
            "growth_rate_metric": "QoQ",
            "avg_growth_rate": round(quarterly["MoM_Growth"].dropna().mean(), 2) if not quarterly.empty else 0.0,
            "x_tick_angle": 0,
        }
        return quarterly, insights_out

    # ─────────────────────────────────────────────────────────────────────────────
    # CASE C: WEEKLY DRILLDOWN
    # ─────────────────────────────────────────────────────────────────────────────
    elif active_granularity == "weekly":
        df_copy = df_active.copy()
        df_copy["Week"] = df_copy["Date"].dt.to_period("W")
        weekly = df_copy.groupby("Week").agg(**agg_dict).reset_index()
        if not has_profit or "Profit" not in weekly.columns:
            weekly["Profit"] = 0.0

        if is_single_year_slice:
            weekly["Month_Label"] = weekly["Week"].apply(lambda w: f"W{w.week:02d}")
            trend_title = f"Weekly Performance Trajectory ({slice_year})"
        else:
            weekly["Month_Label"] = weekly["Week"].apply(lambda w: f"W{w.week:02d} '{str(w.year)[-2:]}")
            min_y = df_active["Date"].dt.year.min()
            max_y = df_active["Date"].dt.year.max()
            trend_title = f"Weekly Trajectory ({min_y} - {max_y})"

        weekly["Period_Label"] = weekly["Month_Label"]
        weekly["MoM_Growth"] = weekly["Revenue"].pct_change() * 100
        weekly["Is_Partial"] = False

        best_w_idx = weekly["Revenue"].idxmax() if not weekly.empty else None
        worst_w_idx = weekly["Revenue"].idxmin() if not weekly.empty else None

        if best_w_idx is not None and worst_w_idx is not None:
            best_w = weekly.loc[best_w_idx, "Month_Label"]
            worst_w = weekly.loc[worst_w_idx, "Month_Label"]
            best_w_rev = float(weekly.loc[best_w_idx, "Revenue"])
            worst_w_rev = float(weekly.loc[worst_w_idx, "Revenue"])
        else:
            best_w, worst_w = "N/A", "N/A"
            best_w_rev, worst_w_rev = 0.0, 0.0

        insights_out = {
            "time_horizon": "weekly",
            "granularity": "weekly",
            "target_year": target_year,
            "horizon_desc": f"Weekly velocity ({len(weekly)} weeks)",
            "trend_title": trend_title,
            "best_period": f"{best_w} {slice_year}" if is_single_year_slice and not best_w.endswith(str(slice_year)) else best_w,
            "worst_period": f"{worst_w} {slice_year}" if is_single_year_slice and not worst_w.endswith(str(slice_year)) else worst_w,
            "best_period_tag": "🏆 Peak Week Velocity",
            "worst_period_tag": "⚠️ Softest Week Velocity",
            "best_period_desc": f"Highest weekly velocity recorded ({sym}{best_w_rev:,.0f}).",
            "worst_period_desc": f"Softest weekly velocity recorded ({sym}{worst_w_rev:,.0f}).",
            "period_guidance": f"Review inventory buffer and delivery schedule ahead of {best_w}.",
            "growth_rate_metric": "WoW",
            "avg_growth_rate": round(weekly["MoM_Growth"].dropna().mean(), 2) if not weekly.empty else 0.0,
            "x_tick_angle": 0,
        }
        return weekly, insights_out

    # ─────────────────────────────────────────────────────────────────────────────
    # CASE C: ANNUAL MACRO DRILLDOWN
    # ─────────────────────────────────────────────────────────────────────────────
    elif active_granularity == "annual":
        df_copy = df_active.copy()
        df_copy["Year"] = df_copy["Date"].dt.year
        annual = df_copy.groupby("Year").agg(**agg_dict).reset_index()
        if not has_profit or "Profit" not in annual.columns:
            annual["Profit"] = 0.0

        annual["Month_Label"] = annual["Year"].astype(str)
        annual["Period_Label"] = annual["Month_Label"]
        annual["MoM_Growth"] = annual["Revenue"].pct_change() * 100
        annual["Is_Partial"] = False

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

        if len(annual) > 1:
            trend_title = f"Annual Macro Growth (FY {annual['Year'].min()} - FY {annual['Year'].max()})"
        else:
            trend_title = f"Annual Performance Trajectory (FY {best_y})"

        insights_out = {
            "time_horizon": "annual",
            "granularity": "annual",
            "target_year": target_year,
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
            "avg_growth_rate": round(annual["MoM_Growth"].dropna().mean(), 2) if not annual.empty else 0.0,
            "x_tick_angle": 0,
        }
        return annual, insights_out

    # ─────────────────────────────────────────────────────────────────────────────
    # CASE D: MONTHLY DRILLDOWN (Default)
    # ─────────────────────────────────────────────────────────────────────────────
    else:
        df_copy = df_active.copy()
        df_copy["Month"] = df_copy["Date"].dt.to_period("M")
        monthly = df_copy.groupby("Month").agg(**agg_dict).reset_index()
        if not has_profit or "Profit" not in monthly.columns:
            monthly["Profit"] = 0.0

        # Continuous monthly reindexing
        if not monthly.empty:
            full_idx = pd.period_range(start=monthly["Month"].min(), end=monthly["Month"].max(), freq="M")
            monthly = monthly.set_index("Month").reindex(full_idx, fill_value=0.0).reset_index()
            monthly = monthly.rename(columns={"index": "Month"})
            if "Orders" in monthly.columns:
                monthly["Orders"] = monthly["Orders"].fillna(0).astype(int)

        if is_single_year_slice:
            # Single year: clean 3-letter months with NO repetitive year suffix!
            # E.g. Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
            monthly["Month_Label"] = monthly["Month"].dt.strftime("%b")
            trend_title = f"Monthly Revenue vs Net Profit ({slice_year})" if has_profit else f"Monthly Revenue Trajectory ({slice_year})"
        else:
            # Multi-year monthly: compact Jan '25, Feb '25
            monthly["Month_Label"] = monthly["Month"].apply(lambda m: f"{m.strftime('%b')} '{str(m.year)[-2:]}")
            min_y = df_active["Date"].dt.year.min()
            max_y = df_active["Date"].dt.year.max()
            trend_title = f"Monthly Trajectory ({min_y} - {max_y})"

        monthly["Period_Label"] = monthly["Month_Label"]
        monthly["MoM_Growth"] = monthly["Revenue"].pct_change() * 100
        monthly["Is_Partial"] = False

        best_m = monthly.loc[monthly["Revenue"].idxmax(), "Month_Label"] if not monthly.empty else "N/A"
        worst_m = monthly.loc[monthly["Revenue"].idxmin(), "Month_Label"] if not monthly.empty else "N/A"
        if best_m == worst_m and len(monthly) > 1:
            other_m = [m for m in monthly["Month_Label"] if m != best_m]
            if other_m:
                worst_m = other_m[0]

        best_m_full = f"{best_m} {slice_year}" if is_single_year_slice and not best_m.endswith(str(slice_year)) else best_m
        worst_m_full = f"{worst_m} {slice_year}" if is_single_year_slice and not worst_m.endswith(str(slice_year)) else worst_m

        insights_out = {
            "time_horizon": "monthly",
            "granularity": "monthly",
            "target_year": target_year,
            "horizon_desc": horizon_info["desc"],
            "trend_title": trend_title,
            "best_period": best_m_full,
            "worst_period": worst_m_full,
            "best_period_tag": "🏆 Peak Monthly Velocity",
            "worst_period_tag": "⚠️ Contraction Window",
            "best_period_desc": "Highest activity concentration recorded across the multi-month period.",
            "worst_period_desc": "Softest period recorded. Primary opportunity for strategic counter-cyclical initiatives.",
            "period_guidance": f"Review capacity and planning ahead of best_m_full, the strongest period in this data.",
            "growth_rate_metric": "MoM",
            "avg_growth_rate": round(monthly["MoM_Growth"].dropna().mean(), 2) if not monthly.empty else 0.0,
            "x_tick_angle": 0,
        }
        return monthly, insights_out


def monthly_trend(df: pd.DataFrame, has_profit: bool = True) -> pd.DataFrame:
    """True calendar-month series (never quarterly/weekly), with gap months,
    NaN-safe growth and partial first/last month detection."""
    work = df[["Date", "Revenue"] + (["Profit"] if has_profit and "Profit" in df.columns else [])].copy()
    work = work.dropna(subset=["Date"])
    work["Month"] = work["Date"].dt.to_period("M")
    agg_dict = {"Revenue": ("Revenue", "sum"), "Orders": ("Revenue", "count")}
    if has_profit and "Profit" in work.columns:
        agg_dict["Profit"] = ("Profit", "sum")

    monthly = work.groupby("Month").agg(**agg_dict)
    if monthly.empty:
        return pd.DataFrame(columns=["Month", "Revenue", "Orders", "Profit", "Month_Label", "MoM_Growth", "Is_Partial"])

    full_idx = pd.period_range(start=monthly.index.min(), end=monthly.index.max(), freq="M")
    monthly = monthly.reindex(full_idx, fill_value=0.0)
    monthly.index.name = "Month"
    monthly = monthly.reset_index()
    monthly["Orders"] = monthly["Orders"].fillna(0).astype(int)
    if "Profit" not in monthly.columns:
        monthly["Profit"] = 0.0

    monthly["Month_Label"] = monthly["Month"].dt.strftime("%b %Y")
    growth = monthly["Revenue"].pct_change() * 100
    monthly["MoM_Growth"] = growth.replace([np.inf, -np.inf], np.nan)

    min_date = work["Date"].min()
    max_date = work["Date"].max()
    monthly["Is_Partial"] = False
    # Partial-month detection only makes sense for dense (daily-ish) data; one row per
    # month dated the 1st would otherwise make every last month look "partial".
    days_per_month = work.groupby("Month")["Date"].apply(lambda d: d.dt.normalize().nunique())
    if len(monthly) >= 2 and float(days_per_month.median()) >= 4:
        if min_date.day > 10:
            monthly.loc[monthly.index[0], "Is_Partial"] = True
        if max_date.day < (pd.Period(max_date, freq="D").days_in_month - 5):
            monthly.loc[monthly.index[-1], "Is_Partial"] = True
    return monthly


def compute_growth_metrics(monthly: pd.DataFrame) -> dict:
    """Growth stats from a TRUE monthly series. Partial months are excluded from
    growth maths; too little history yields honest 'not enough history' labels."""
    out = {"cmgr": None, "avg_mom_growth": None, "growth_label": "Not enough history",
           "growth_arrow": "", "partial_months": [], "n_full_months": 0}
    if monthly is None or monthly.empty:
        return out
    partial = monthly["Is_Partial"].astype(bool) if "Is_Partial" in monthly else pd.Series(False, index=monthly.index)
    out["partial_months"] = monthly.loc[partial, "Month_Label"].tolist()
    full = monthly[~partial].copy()
    out["n_full_months"] = len(full)
    if len(full) < 3:
        return out
    g = full["Revenue"].pct_change() * 100
    g = g.replace([np.inf, -np.inf], np.nan).dropna()
    out["avg_mom_growth"] = round(float(g.mean()), 2) if not g.empty else None
    first, last = float(full["Revenue"].iloc[0]), float(full["Revenue"].iloc[-1])
    if first > 0 and last > 0:
        cmgr = ((last / first) ** (1.0 / (len(full) - 1)) - 1.0) * 100.0
        out["cmgr"] = round(cmgr, 2)
        out["growth_arrow"] = "↑" if cmgr >= 0 else "↓"
        sign = "+" if cmgr >= 0 else ""
        out["growth_label"] = f"{out['growth_arrow']} {sign}{cmgr:.1f}% CMGR"
    return out


def detect_time_series_anomalies(monthly: pd.DataFrame, z_threshold: float = 2.0, mom_threshold: float = 40.0, currency_symbol: str = "$") -> list:
    """
    Robust statistical anomaly detection on time-series monthly revenue using Median
    and Median Absolute Deviation (MAD) to prevent normal fluctuations from triggering alerts.
    Identifies significant surges and contractions with partial-month awareness.
    """
    if monthly is None or len(monthly) < 6 or "Revenue" not in monthly.columns:
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
        if is_partial:
            continue  # incomplete months are never flagged as anomalies

        is_spike = (z_robust >= z_threshold) or (mom >= mom_threshold and z_robust >= 1.5)
        is_drop  = (z_robust <= -z_threshold) or (mom <= -mom_threshold and z_robust <= -1.5)

        if is_spike or is_drop:
            anom_type = "Surge" if is_spike else "Dip"
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
                "summary": f"{row.get('Month_Label', 'Month')}: notable {anom_type.lower()} to {currency_symbol}{r_val:,.0f} ({z_robust:+.2f}σ vs. median, {pct_diff:+.1f}%){partial_note}",
            })

    return sorted(anomalies, key=lambda a: abs(a["z_score"]), reverse=True)


def category_breakdown(df: pd.DataFrame, has_profit: bool = True, max_categories: int = 12) -> pd.DataFrame:
    agg_dict = {"Revenue": ("Revenue", "sum"), "Orders": ("Revenue", "count")}
    if has_profit and "Profit" in df.columns:
        agg_dict["Profit"] = ("Profit", "sum")
        df = df.assign(_Rev_matched=df["Revenue"].where(df["Profit"].notna(), 0.0))
        agg_dict["_Rev_matched"] = ("_Rev_matched", "sum")

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
        other_matched = float(other_slice["_Rev_matched"].sum()) if "_Rev_matched" in other_slice.columns else other_rev

        other_row = pd.DataFrame([{
            "Category": f"Other ({len(other_slice)} items)",
            "Revenue": other_rev,
            "Orders": other_orders,
            "Profit": other_profit,
            **({"_Rev_matched": other_matched} if "_Rev_matched" in cat.columns else {}),
        }])
        cat = pd.concat([top_slice, other_row], ignore_index=True)
    else:
        cat = cat.sort_values("Revenue", ascending=False)

    if has_profit and "Profit" in cat.columns:
        denom = cat["_Rev_matched"] if "_Rev_matched" in cat.columns else cat["Revenue"]
        cat["Margin_%"] = (cat["Profit"] / denom.replace(0, np.nan) * 100).fillna(0.0).round(2)
        cat = cat.drop(columns=["_Rev_matched"], errors="ignore")
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


def infer_mapping(data, report_mode: str = "Sales & Retail Performance") -> dict:
    """
    Intelligently auto-detects semantic column roles (date, revenue, profit, cost, category, region, product, channel)
    from any DataFrame or list of column names using a resilient 3-pass strategy:
    1. Exact case-insensitive match
    2. Tokenized word boundary match (prevents 'unit' matching 'unit_price')
    3. Negative exclusion substring match
    """
    if isinstance(data, pd.DataFrame):
        cols = data.columns.tolist()
    elif isinstance(data, (list, tuple, pd.Index)):
        cols = list(data)
    else:
        cols = []

    if not cols:
        return {}

    def fcol(candidates, exclude=None):
        ex = [e.lower() for e in (exclude or [])]
        for c in candidates:
            for col in cols:
                col_l = str(col).lower()
                if any(e in col_l for e in ex):
                    continue
                if c.lower() == col_l:
                    return col
        for c in candidates:
            for col in cols:
                col_l = str(col).lower()
                if any(e in col_l for e in ex):
                    continue
                tokens = re.split(r'[\s_\-]+', col_l)
                if c.lower() in tokens:
                    return col
        for c in candidates:
            for col in cols:
                col_l = str(col).lower()
                if any(e in col_l for e in ex):
                    continue
                if c.lower() in col_l:
                    return col
        return cols[0]

    def fcol_opt(candidates, exclude=None):
        ex = [e.lower() for e in (exclude or [])]
        for c in candidates:
            for col in cols:
                col_l = str(col).lower()
                if any(e in col_l for e in ex):
                    continue
                if c.lower() == col_l:
                    return col
        for c in candidates:
            for col in cols:
                col_l = str(col).lower()
                if any(e in col_l for e in ex):
                    continue
                tokens = re.split(r'[\s_\-]+', col_l)
                if c.lower() in tokens:
                    return col
        for c in candidates:
            for col in cols:
                col_l = str(col).lower()
                if any(e in col_l for e in ex):
                    continue
                if c.lower() in col_l:
                    return col
        return None

    mode = report_mode or "Sales & Retail Performance"
    conv_col = None
    if "Marketing" in mode:
        date_col    = fcol(["date", "time", "day", "month", "period"])
        revenue_col = fcol(["spend", "ad_spend", "budget", "investment", "revenue", "sales", "cost", "amount", "total"], exclude=["price", "unit_price"])
        profit_col  = fcol_opt(["return_value", "return", "revenue_generated", "conversion_value", "attributed_revenue", "profit"], exclude=["unit_cost"])
        conv_col    = fcol_opt(["conversions", "conversion", "leads", "acquisitions", "signups", "sign_ups", "purchases"])
        cost_col    = None
        cat_col     = fcol_opt(["channel", "campaign", "network", "source", "medium", "category", "type"], exclude=["price", "unit_price", "cost"])
        region_col  = fcol_opt(["region", "country", "market", "geo", "location", "city", "audience"])
        prod_col    = fcol_opt(["campaign", "ad", "creative", "product", "item"])
        chan_col    = fcol_opt(["channel", "platform", "network", "source", "medium"])
    elif "Operations" in mode:
        date_col    = fcol(["date", "time", "day", "month", "period"])
        revenue_col = fcol(["budget", "allocated", "target", "total_budget", "revenue", "amount", "total"], exclude=["price", "unit_price", "rate"])
        profit_col  = fcol_opt(["actual", "actual_expenses", "expense", "expenses", "spend", "cost"], exclude=["unit_cost", "price", "variance"])
        cost_col    = None
        cat_col     = fcol_opt(["category", "department", "dept", "cost_center", "function", "type", "unit"], exclude=["price", "cost", "unit_price", "rate"])
        region_col  = fcol_opt(["facility", "branch", "site", "warehouse", "region", "location", "plant"])
        prod_col    = fcol_opt(["item", "task", "work_order", "expense_item", "product"])
        chan_col    = fcol_opt(["channel", "vendor", "supplier", "team"])
    else:  # Sales & Retail Performance
        date_col    = fcol(["date", "time", "day", "month"])
        revenue_col = fcol(["revenue", "sales", "gross_sales", "amount", "income", "total"], exclude=["price", "unit_price", "quantity", "units"])
        profit_col  = fcol_opt(["profit", "margin", "net", "net_profit"], exclude=["unit_cost", "margin_%"])
        cost_col    = fcol_opt(["cost", "expense", "cogs"], exclude=["unit_cost"])
        cat_col     = fcol_opt(["category", "type", "segment", "department"], exclude=["price", "unit_price", "cost"])
        region_col  = fcol_opt(["region", "country", "area", "zone", "location", "territory", "city", "state"])
        prod_col    = fcol_opt(["product", "sku", "item", "description"])
        chan_col    = fcol_opt(["channel", "store", "platform", "source", "outlet"])

    return {
        "date": date_col,
        "revenue": revenue_col,
        "profit": profit_col,
        "cost": cost_col,
        "conversions": conv_col,
        "category": cat_col,
        "region": region_col,
        "product": prod_col or cat_col,
        "channel": chan_col,
    }


def build_report_from_df(df: pd.DataFrame, mapping: dict = None, report_mode: str = "Sales & Retail Performance", currency_symbol: str = "$",
                         drop_exact_duplicates: bool = False, id_column: str = None, source_notes: list = None,
                         missing_policy: dict = None, derive_relations: bool = True, **kwargs) -> dict:
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

    # 3. Summary rows: only "Total"-style labels in the LAST 5 rows (never "sum"/"summary",
    #    never mid-file) so real data such as a "Summary" campaign is not removed.
    summary_keywords = {"total", "grand total", "subtotal", "sub total", "totals"}
    is_summary_row = pd.Series(False, index=clean_df.index)
    tail_idx = clean_df.index[-5:]
    for col in clean_df.columns:
        if not pd.api.types.is_numeric_dtype(clean_df[col]):
            matches = clean_df[col].astype(str).str.strip().str.lower().isin(summary_keywords)
            is_summary_row = is_summary_row | (matches & clean_df.index.isin(tail_idx))

    if is_summary_row.any():
        summary_count = int(is_summary_row.sum())
        summary_rows = clean_df[is_summary_row].copy()
        summary_rows["quarantine_reason"] = "Summary / Total row at end of file (prevented double-counting)"
        quarantine_records.append(summary_rows)
        clean_df = clean_df[~is_summary_row].copy()
        audit_trail.append(f"Excluded {summary_count} trailing summary row(s) ('Total'/'Grand Total') to prevent double-counting")
    else:
        summary_count = 0

    # 4. Duplicates: identical rows are often legitimate (two identical sales). They are KEPT by
    #    default and only removed when the user opts in, or by an explicit ID column.
    dup_count = 0
    detected_dups = int(clean_df.duplicated(keep="first").sum())
    if id_column and id_column in clean_df.columns:
        dup_mask = clean_df.duplicated(subset=[id_column], keep="first") & clean_df[id_column].notna()
        dup_reason = f"Duplicate ID in '{id_column}'"
    elif drop_exact_duplicates:
        dup_mask = clean_df.duplicated(keep="first")
        dup_reason = "Exact duplicate row (removed at user request)"
    else:
        dup_mask = pd.Series(False, index=clean_df.index)
        dup_reason = ""
    if dup_mask.any():
        dup_count = int(dup_mask.sum())
        dup_rows = clean_df[dup_mask].copy()
        dup_rows["quarantine_reason"] = dup_reason
        quarantine_records.append(dup_rows)
        clean_df = clean_df[~dup_mask].copy()
        audit_trail.append(f"Removed {dup_count} duplicate row(s): {dup_reason}")
    elif detected_dups > 0:
        audit_trail.append(f"{detected_dups} exact-duplicate row(s) detected and KEPT (they may be genuine repeat transactions; enable 'Remove exact duplicates' to drop them)")

    active_mapping = mapping if mapping is not None else infer_mapping(clean_df, report_mode=report_mode)
    has_mapped_profit = False
    has_mapped_cost   = False

    if active_mapping:
        target_name_map = {
            "date": "Date",
            "revenue": "Revenue",
            "profit": "Profit",
            "cost": "Cost",
            "category": "Category",
            "region": "Region",
            "product": "Product",
            "channel": "Channel",
            "quantity": "Quantity",
            "conversions": "Conversions",
        }
        for target, src in active_mapping.items():
            target_col = target_name_map.get(target.lower(), target.capitalize())
            if not src or src == "None / Not Available":
                if target_col in clean_df.columns:
                    clean_df = clean_df.drop(columns=[target_col])
            elif src in clean_df.columns or src in df.columns:
                source_series = clean_df[src].copy() if src in clean_df.columns else df[src].copy()
                if target.lower() == "profit":
                    has_mapped_profit = True
                elif target.lower() == "cost":
                    has_mapped_cost = True
                clean_df[target_col] = source_series

    # Bulletproof guard against duplicate column names from any source
    clean_df = clean_df.loc[:, ~clean_df.columns.duplicated()]

    # Drop rows that are completely empty / all NaN across all columns
    initial_len = len(clean_df)
    clean_df = clean_df.dropna(how="all")
    dropped_empty_rows = initial_len - len(clean_df)
    if dropped_empty_rows > 0:
        audit_trail.append(f"Dropped {dropped_empty_rows} completely blank row(s)")

    synthetic_columns = []
    pre_quarantine_len = len(clean_df)

    # Standardize Date column. Invalid dates are QUARANTINED, never invented.
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
        bad_dates = parsed_dates.isna()
        if len(clean_df) and bad_dates.mean() > 0.5:
            raise ValueError("More than half of the rows have a Date value that could not be read. Check that the Date column is mapped correctly.")
        if bad_dates.any():
            bad = clean_df[bad_dates].copy()
            bad["quarantine_reason"] = "Missing or unreadable date"
            quarantine_records.append(bad)
            audit_trail.append(f"Quarantined {int(bad_dates.sum())} row(s) with missing/unreadable dates (not imputed)")
            clean_df = clean_df[~bad_dates].copy()
            parsed_dates = parsed_dates[~bad_dates]
        clean_df["Date"] = parsed_dates
    else:
        fallback_year = datetime.date.today().year
        clean_df["Date"] = pd.date_range(start=f"{fallback_year}-01-01", periods=len(clean_df), freq="D")
        synthetic_columns.append("Date")
        audit_trail.append("No Date column mapped: a sequential placeholder timeline was generated, so time-based trends are NOT real")

    # Revenue: rows with missing/unreadable revenue are quarantined instead of counted as 0.
    if "Revenue" in clean_df.columns:
        rev, sym_cnt, rev_bad = sanitize_numeric_with_mask(clean_df["Revenue"])
        if len(clean_df) and rev_bad.mean() > 0.5:
            raise ValueError("More than half of the rows have a Revenue/Spend/Budget value that could not be read. Check the column mapping.")
        symbols_cleaned_total += sym_cnt
        if sym_cnt > 0:
            audit_trail.append(f"Standardized {sym_cnt} formatted value(s)/symbol(s) in Revenue")
        if rev_bad.any():
            bad = clean_df[rev_bad].copy()
            bad["quarantine_reason"] = "Missing or unreadable Revenue value"
            quarantine_records.append(bad)
            audit_trail.append(f"Quarantined {int(rev_bad.sum())} row(s) with missing/unreadable Revenue (not zero-filled)")
            clean_df = clean_df[~rev_bad].copy()
            rev = rev[~rev_bad]
        clean_df["Revenue"] = rev
    else:
        raise ValueError("No Revenue / Spend / Budget column is mapped.")

    from data_quality import apply_policies, derive_missing, missing_profile
    is_sales = "Sales" in (report_mode or "Sales")
    blank_counts = {}

    def _opt_numeric(col, label):
        """Parse an optional numeric column. Blanks STAY blank (NaN): a missing Cost is not a Cost of 0."""
        nonlocal symbols_cleaned_total
        cleaned, fmt_cnt, bad = sanitize_numeric_with_mask(clean_df[col])
        symbols_cleaned_total += fmt_cnt
        if fmt_cnt > 0:
            audit_trail.append(f"Standardized {fmt_cnt} formatted value(s) in {label}")
        n_bad = int(bad.sum())
        if n_bad > 0:
            blank_counts[col] = n_bad
        return cleaned

    cost_mapped = bool(has_mapped_cost and "Cost" in clean_df.columns)
    profit_mapped = bool(has_mapped_profit and "Profit" in clean_df.columns)

    if cost_mapped:
        clean_df["Cost"] = _opt_numeric("Cost", "Cost")
    else:
        clean_df["Cost"] = 0.0
        synthetic_columns.append("Cost")

    if profit_mapped:
        clean_df["Profit"] = _opt_numeric("Profit", "Profit/Return/Actual")
        has_profit = True
    elif cost_mapped and is_sales:
        clean_df["Profit"] = clean_df["Revenue"] - clean_df["Cost"]   # stays NaN where Cost is blank
        has_profit = True
        audit_trail.append("Derived Profit as Revenue - Cost (no Profit column mapped)")
    else:
        clean_df["Profit"] = 0.0
        has_profit = False
        synthetic_columns.append("Profit")

    if "Conversions" in clean_df.columns:
        clean_df["Conversions"] = _opt_numeric("Conversions", "Conversions")

    # Quantity: kept exactly as provided (no clipping, no invented default).
    if "Quantity" in clean_df.columns:
        clean_df["Quantity"] = _opt_numeric("Quantity", "Quantity")

    # Exact relational fills (profit = revenue - cost etc.) come BEFORE any statistical fill.
    values_derived_total = 0
    identity_report = []
    if is_sales and cost_mapped and profit_mapped and derive_relations:
        dres = derive_missing(clean_df, {"revenue": "Revenue", "cost": "Cost", "profit": "Profit"})
        clean_df = dres.df
        identity_report = dres.identity_report
        values_derived_total = int(sum(m.sum() for m in dres.derived_masks.values()))
        audit_trail.extend(dres.log)
        for item in identity_report:
            if item["violations"]:
                audit_trail.append(f"Check: {item['violations']} of {item['checked_rows']} row(s) break '{item['relation']}' (possible data error)")

    # Profile what is still blank in the columns the user may want to handle
    handle_cols = [c for c in ("Cost", "Profit", "Quantity", "Conversions") if c in clean_df.columns and c not in synthetic_columns]
    dq_profile = missing_profile(clean_df, handle_cols, "Date") if handle_cols else pd.DataFrame()
    for _, r_ in dq_profile.iterrows():
        if r_["missing_n"] > 0:
            audit_trail.append(f"'{r_['column']}' is blank in {r_['missing_n']} row(s) ({r_['missing_pct']}%) - kept blank and excluded from calculations that need it")

    # User-chosen handling per column (default: keep blank)
    estimated_cells = {}
    if missing_policy:
        usable = {c: p for c, p in missing_policy.items() if c in handle_cols}
        pres = apply_policies(clean_df, usable)
        if pres.rows_dropped:
            dropped_mask = ~clean_df.index.isin(pres.df.index)
            dropped_rows = clean_df[dropped_mask].copy()
            dropped_rows["quarantine_reason"] = "Removed at your request (missing value in a column you chose to drop on)"
            quarantine_records.append(dropped_rows)
        clean_df = pres.df
        audit_trail.extend(pres.log)
        estimated_cells = {c: int(m.sum()) for c, m in pres.filled_masks.items()}
        nulls_imputed_total += sum(estimated_cells.values())

    if has_profit and clean_df["Profit"].notna().sum() == 0:
        has_profit = False
        clean_df["Profit"] = 0.0
        if "Profit" not in synthetic_columns:
            synthetic_columns.append("Profit")
        audit_trail.append("Profit has no measured values, so profit-based metrics are not shown")

    clean_row_count = len(clean_df)
    quarantined_total = raw_row_count - clean_row_count
    dropped_rows_total = quarantined_total
    retention_pct = round((clean_row_count / raw_row_count * 100), 1) if raw_row_count > 0 else 100.0
    if clean_row_count == 0:
        raise ValueError("No usable rows remain after validation. Check the Date and Revenue column mapping.")

    min_date = clean_df["Date"].min()
    max_date = clean_df["Date"].max()
    date_range_str = f"{min_date.strftime('%b %d, %Y')} – {max_date.strftime('%b %d, %Y')}" if pd.notna(min_date) else "N/A"

    audit_trail.insert(0, f"Ingested {raw_row_count:,} raw records; {clean_row_count:,} usable ({retention_pct}% retained)")
    for _n in (source_notes or []):
        audit_trail.insert(1, _n)
    audit_trail.append(f"Time coverage: {date_range_str}")

    # 5. Text columns: trim/collapse whitespace and merge case-only variants. No Title Case.
    case_merged = 0
    for col in clean_df.columns:
        if not pd.api.types.is_numeric_dtype(clean_df[col]) and not pd.api.types.is_datetime64_any_dtype(clean_df[col]):
            clean_df[col] = normalize_text_series(clean_df[col], to_title_case=False)
            if str(col).lower() in {"category", "region", "product", "channel", "department", "cost_center"}:
                clean_df[col], n_changed = consolidate_case_variants(clean_df[col])
                case_merged += n_changed
    audit_trail.append("Trimmed whitespace in text fields" + (f"; merged {case_merged} case-only spelling variant(s)" if case_merged else ""))

    if "Category" not in clean_df.columns:
        clean_df["Category"] = "All Categories"
        synthetic_columns.append("Category")
    if "Region" not in clean_df.columns:
        clean_df["Region"] = "All Regions"
        synthetic_columns.append("Region")
    if "Product" not in clean_df.columns:
        clean_df["Product"] = clean_df["Category"]
        synthetic_columns.append("Product")
    if synthetic_columns:
        audit_trail.append("Placeholder column(s) created for analysis (not in your file): " + ", ".join(synthetic_columns))

    # 6. Assemble quarantined rows dataset
    if quarantine_records:
        quarantined_df = pd.concat(quarantine_records, ignore_index=True)
    else:
        quarantined_df = pd.DataFrame(columns=list(clean_df.columns) + ["quarantine_reason"])

    # Honest health score: driven by rows lost and values assumed, not by cosmetic fixes.
    quarantined_pct = (len(quarantined_df) / raw_row_count * 100) if raw_row_count else 0.0
    real_opt = [c for c in handle_cols if c in clean_df.columns]
    max_blank_pct = max([float(clean_df[c].isna().mean() * 100) for c in real_opt], default=0.0)
    penalty = round(quarantined_pct) + min(10, nulls_imputed_total) + min(10, round(max_blank_pct / 5)) + (5 if "Date" in synthetic_columns else 0)
    health_score = int(max(0, 100 - penalty))
    if len(quarantined_df) == 0 and nulls_imputed_total == 0 and max_blank_pct == 0 and "Date" not in synthetic_columns:
        health_status = "No issues found" if symbols_cleaned_total == 0 else f"Clean ({symbols_cleaned_total} formatted values standardized)"
    else:
        bits = []
        if len(quarantined_df): bits.append(f"{len(quarantined_df)} row(s) quarantined")
        if nulls_imputed_total: bits.append(f"{nulls_imputed_total} value(s) estimated")
        if max_blank_pct > 0: bits.append(f"up to {max_blank_pct:.0f}% blank in optional columns")
        if "Date" in synthetic_columns: bits.append("placeholder timeline used")
        health_status = "Review: " + ", ".join(bits)

    hygiene = {
        "raw_row_count": raw_row_count,
        "clean_row_count": clean_row_count,
        "dropped_rows_count": dropped_rows_total,
        "rows_retained_pct": retention_pct,
        "currency_symbols_stripped": symbols_cleaned_total,
        "missing_values_imputed": nulls_imputed_total,
        "duplicates_removed": dup_count,
        "duplicates_detected": detected_dups,
        "summary_rows_removed": summary_count,
        "quarantined_rows_count": len(quarantined_df),
        "synthetic_columns": synthetic_columns,
        "values_derived": values_derived_total,
        "estimated_cells": estimated_cells,
        "missing_profile": dq_profile.to_dict("records") if len(dq_profile) else [],
        "identity_report": identity_report,
        "date_range": date_range_str,
        "health_score": health_score,
        "health_status": health_status,
        "audit_log": audit_trail,
    }

    return _assemble_report(clean_df, has_profit, report_mode, currency_symbol, hygiene, quarantined_df)


def build_scoped_report(base_report: dict, scope_id: str, currency_symbol: str = None) -> dict:
    """Return a complete report (KPIs, trend, breakdowns, insights, anomalies) for a time scope.
    Never mutates base_report. Hygiene/quarantine stay those of the full dataset."""
    if not scope_id or scope_id == "all":
        out = dict(base_report)
        out.setdefault("scope_id", "all")
        out.setdefault("scope_name", "Full Period")
        return out
    clean_df = base_report["df"]
    scoped_df, scope_name = filter_df_by_time_scope(clean_df, scope_id)
    if scoped_df is None or scoped_df.empty:
        return build_scoped_report(base_report, "all", currency_symbol)
    sym = currency_symbol or base_report.get("meta", {}).get("currency_symbol", "$")
    return _assemble_report(
        scoped_df, bool(base_report["kpis"].get("has_profit", True)), base_report.get("report_mode", "Sales & Retail Performance"),
        sym, base_report.get("hygiene", {}), base_report.get("quarantined_df"),
        time_scopes=base_report.get("time_scopes"), scope_id=scope_id, scope_name=scope_name,
    )


def _assemble_report(clean_df: pd.DataFrame, has_profit: bool, report_mode: str, currency_symbol: str,
                     hygiene: dict, quarantined_df: pd.DataFrame, time_scopes: dict = None,
                     scope_id: str = "all", scope_name: str = "Full Period") -> dict:
    """Compute every KPI/insight from an already-cleaned frame. Used for both the full
    dataset and any time-scoped slice so the two can never drift apart."""
    kpis     = compute_kpis(clean_df, has_profit=has_profit, report_mode=report_mode)
    if time_scopes is None:
        time_scopes = get_available_time_scopes(clean_df)
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
    monthly_series = monthly_trend(clean_df, has_profit=has_profit)
    growth = compute_growth_metrics(monthly_series)
    cmgr = growth["cmgr"]
    avg_mom_growth = growth["avg_mom_growth"]
    growth_arrow = growth["growth_arrow"]
    growth_label = growth["growth_label"]
    partial_months = growth["partial_months"]

    # best / worst from full (non-partial) true months when we have enough of them
    full_months = monthly_series[~monthly_series["Is_Partial"]] if not monthly_series.empty else monthly_series
    if len(full_months) >= 3:
        best_month = str(full_months.loc[full_months["Revenue"].idxmax(), "Month_Label"])
        worst_month = str(full_months.loc[full_months["Revenue"].idxmin(), "Month_Label"])

    mode_top_basis = ("highest spend" if "Marketing" in report_mode else
                      ("largest budget" if "Operations" in report_mode else "highest revenue"))
    top_cat     = category.iloc[0]["Category"] if not category.empty else "General"
    top_region  = region.iloc[0]["Region"] if not region.empty else "Global"
    top_channel = channels.iloc[0]["Channel"] if has_channel and not channels.empty else None

    anomalies = detect_time_series_anomalies(monthly_series, currency_symbol=currency_symbol)
    has_anomalies = len(anomalies) > 0
    if has_anomalies:
        top_anom = anomalies[0]
        anomaly_headline = f"{top_anom['period']} showed a notable {top_anom['type'].lower()} ({top_anom['pct_diff_mean']:+.1f}% vs. typical month)."
    else:
        anomaly_headline = "No unusual month-to-month swings detected." if len(monthly_series) >= 6 else "Not enough monthly history to assess anomalies."

    detected_year = int(clean_df["Date"].dt.year.mode()[0]) if "Date" in clean_df.columns and not clean_df["Date"].dropna().empty else datetime.date.today().year

    meta_dict = get_mode_kpi_labels(report_mode)
    meta_dict["currency_symbol"] = currency_symbol
    meta_dict["trend_title"] = time_insights.get("trend_title", meta_dict.get("trend_title", "Performance Trajectory"))
    meta_dict["time_horizon"] = horizon_info["horizon"]
    meta_dict["horizon_desc"] = horizon_info["desc"]
    meta_dict["detected_year"] = detected_year

    return {
        "df":             clean_df,
        "quarantined_df": quarantined_df,
        "kpis":           kpis,
        "monthly":        monthly,
        "monthly_series": monthly_series,
        "category":       category,
        "region":         region,
        "top_products":   products,
        "channels":       channels,
        "report_mode":  report_mode,
        "meta":         meta_dict,
        "time_scopes":  time_scopes,
        "insights": {
            "best_month":        best_month,
            "worst_month":       worst_month,
            "best_period":       best_period,
            "worst_period":      worst_period,
            "detected_year":     detected_year,
            "best_period_tag":   time_insights.get("best_period_tag", "🏆 Peak Performance Period"),
            "worst_period_tag":  time_insights.get("worst_period_tag", "⚠️ Contraction Window"),
            "best_period_desc":  time_insights.get("best_period_desc", "Highest activity concentration recorded."),
            "worst_period_desc": time_insights.get("worst_period_desc", "Softest period recorded. Primary opportunity for strategic initiatives."),
            "period_guidance":   time_insights.get("period_guidance", f"Review capacity and planning ahead of best_period, the strongest period in this data."),
            "trend_title":       time_insights.get("trend_title", "Performance Trajectory"),
            "time_horizon":      horizon_info["horizon"],
            "horizon_desc":      horizon_info["desc"],
            "avg_mom_growth":    avg_mom_growth,
            "cmgr":              cmgr,
            "growth_arrow":      growth_arrow,
            "growth_label":      growth_label,
            "partial_months":    partial_months,
            "top_basis":         mode_top_basis,
            "top_category":      top_cat,
            "top_region":        top_region,
            "top_channel":       top_channel,
            "has_channel":       has_channel,
            "anomalies":         anomalies,
            "has_anomalies":     has_anomalies,
            "anomaly_headline":  anomaly_headline,
        },
        "hygiene": hygiene,
        "scope_id": scope_id,
        "scope_name": scope_name,
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

"""export_utils.py - on-demand Excel export of cleaned data, audit trail and quarantined rows."""
import io
import re
import pandas as pd

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_cell_for_spreadsheet(val):
    """Prefix dangerous formula-triggering strings with `'`, leaving signed numeric strings, numbers, dates, and None untouched."""
    if isinstance(val, str) and val.startswith(_FORMULA_PREFIXES):
        if re.fullmatch(r"[+-]\d+(?:\.\d+)?", val.strip()):
            return val
        return "'" + val
    return val


def sanitize_df_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with formula-injection string cells neutralized."""
    if df is None:
        return df
    out = df.copy()
    for col in out.columns:
        if isinstance(out[col].dtype, pd.CategoricalDtype):
            out[col] = [sanitize_cell_for_spreadsheet(v) for v in out[col].astype(object)]
        elif out[col].dtype == object or pd.api.types.is_string_dtype(out[col].dtype):
            out[col] = [sanitize_cell_for_spreadsheet(v) for v in out[col]]
    return out


def _autofit_columns(ws, get_column_letter_fn, min_width: int = 12, max_width: int = 60):
    for col in ws.columns:
        if not col:
            continue
        col_letter = get_column_letter_fn(col[0].column)
        max_len = max((len(str(cell.value or "")) for cell in col), default=0)
        ws.column_dimensions[col_letter].width = min(max(max_len + 4, min_width), max_width)


def generate_cleaned_workbook(clean_df: pd.DataFrame, hygiene: dict, quarantined_df: pd.DataFrame, currency_symbol: str = "$") -> bytes:
    from openpyxl.worksheet.table import Table, TableStyleInfo
    from openpyxl.utils import get_column_letter

    hygiene = hygiene or {}
    output = io.BytesIO()
    sym = currency_symbol if currency_symbol else "$"
    curr_fmt = f'"{sym}"#,##0.00'

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df = clean_df.copy()
        # Only export what the user's file contained: drop placeholder columns we invented
        synthetic = [c for c in hygiene.get("synthetic_columns", []) if c in export_df.columns]
        export_df = export_df.drop(columns=synthetic)
        # Keep Date as native Python date objects so openpyxl writes true Excel dates
        if "Date" in export_df.columns:
            export_df["Date"] = pd.to_datetime(export_df["Date"], errors="coerce").dt.date
        export_df = sanitize_df_for_export(export_df)

        export_df.to_excel(writer, sheet_name="Cleaned_Data", index=False)

        # ── 1. Format Cleaned_Data as an Official Excel Table ────────────────
        ws_clean = writer.sheets["Cleaned_Data"]
        max_row = len(export_df) + 1  # include header row
        max_col = len(export_df.columns)

        if len(export_df) > 0 and max_col > 0:
            max_col_letter = get_column_letter(max_col)
            date_col_indices = set()
            curr_col_indices = set()
            int_col_indices  = set()

            for c_idx, col_name in enumerate(export_df.columns, start=1):
                col_l = str(col_name).lower()
                if "date" in col_l:
                    date_col_indices.add(c_idx)
                elif any(k in col_l for k in ["revenue", "profit", "cost", "spend", "budget", "aov", "price"]):
                    curr_col_indices.add(c_idx)
                elif any(k in col_l for k in ["quantity", "orders", "units", "conversions", "count"]):
                    int_col_indices.add(c_idx)

            # Apply true Excel number_format rules
            for row in ws_clean.iter_rows(min_row=2, max_row=max_row, min_col=1, max_col=max_col):
                for cell in row:
                    if cell.column in date_col_indices:
                        cell.number_format = 'yyyy-mm-dd'
                    elif cell.column in curr_col_indices and isinstance(cell.value, (int, float)):
                        cell.number_format = curr_fmt
                    elif cell.column in int_col_indices and isinstance(cell.value, (int, float)):
                        cell.number_format = '#,##0'

            # Create Table Object with Banded Rows & Filter Dropdowns
            tab_clean = Table(displayName="CleanedDataTable", ref=f"A1:{max_col_letter}{max_row}")
            tab_clean.tableStyleInfo = TableStyleInfo(
                name="TableStyleMedium9",
                showFirstColumn=False,
                showLastColumn=False,
                showRowStripes=True,
                showColumnStripes=False
            )
            ws_clean.add_table(tab_clean)

        # Auto-fit column widths
        if max_col > 0:
            _autofit_columns(ws_clean, get_column_letter)

        # ── 2. Format Audit_Trail Sheet ──────────────────────────────────────
        audit_summary = [
            {"Metric": "Overall Data Health Score", "Value": f"{hygiene.get('health_score', 100)}% ({hygiene.get('health_status', 'Certified Clean')})"},
            {"Metric": "Raw Records Ingested", "Value": hygiene.get("raw_row_count", len(clean_df))},
            {"Metric": "Cleaned Records Retained", "Value": hygiene.get("clean_row_count", len(clean_df))},
            {"Metric": "Retention Rate", "Value": f"{hygiene.get('rows_retained_pct', 100.0)}%"},
            {"Metric": "Duplicates Removed", "Value": hygiene.get("duplicates_removed", 0)},
            {"Metric": "Summary Rows Excluded", "Value": hygiene.get("summary_rows_removed", 0)},
            {"Metric": "Blank / Dropped Rows", "Value": hygiene.get("dropped_rows_count", 0)},
            {"Metric": "Quarantined Rows Count", "Value": hygiene.get("quarantined_rows_count", len(quarantined_df) if quarantined_df is not None else 0)},
            {"Metric": "Currency Symbols & Formats Sanitized", "Value": hygiene.get("currency_symbols_stripped", 0)},
            {"Metric": "Missing / Null Values Imputed", "Value": hygiene.get("missing_values_imputed", 0)},
            {"Metric": "Validated Date Timeline", "Value": hygiene.get("date_range", "N/A")},
        ]
        sanitize_df_for_export(pd.DataFrame(audit_summary)).to_excel(writer, sheet_name="Audit_Trail", startrow=0, index=False)

        if hygiene.get("audit_log"):
            df_log = sanitize_df_for_export(pd.DataFrame({"Step": range(1, len(hygiene["audit_log"]) + 1), "Audit Action Completed": hygiene["audit_log"]}))
            df_log.to_excel(writer, sheet_name="Audit_Trail", startrow=len(audit_summary) + 3, index=False)

        ws_audit = writer.sheets["Audit_Trail"]
        _autofit_columns(ws_audit, get_column_letter)

        # ── 3. Format Quarantined_Rows Sheet ─────────────────────────────────
        if quarantined_df is not None and not quarantined_df.empty and len(quarantined_df.columns) > 0:
            q_export_df = sanitize_df_for_export(quarantined_df)
            q_export_df.to_excel(writer, sheet_name="Quarantined_Rows", index=False)
            ws_quar = writer.sheets["Quarantined_Rows"]
            q_max_row = len(q_export_df) + 1
            q_max_col = len(q_export_df.columns)
            q_max_col_letter = get_column_letter(q_max_col)

            tab_quar = Table(displayName="QuarantinedRowsTable", ref=f"A1:{q_max_col_letter}{q_max_row}")
            tab_quar.tableStyleInfo = TableStyleInfo(
                name="TableStyleMedium4",
                showFirstColumn=False,
                showLastColumn=False,
                showRowStripes=True,
                showColumnStripes=False
            )
            ws_quar.add_table(tab_quar)
            _autofit_columns(ws_quar, get_column_letter)
        else:
            df_clean_msg = pd.DataFrame([{"Status": "Zero Quarantined Rows", "Message": "All raw rows passed validation and were successfully retained in Cleaned_Data."}])
            df_clean_msg.to_excel(writer, sheet_name="Quarantined_Rows", index=False)
            ws_quar = writer.sheets["Quarantined_Rows"]
            _autofit_columns(ws_quar, get_column_letter)

    return output.getvalue()

"""io_utils.py - shared file reading for the web app and run_pipeline.py."""
import io
import os
import pandas as pd


def read_tabular(name: str, file_bytes: bytes, sheet=0) -> tuple:
    """Parse CSV/Excel bytes. Returns (DataFrame, notes[list of str]).
    CSV: tries utf-8-sig -> utf-8 -> cp1252 -> latin1 with delimiter sniffing."""
    lower = name.lower()
    notes = []
    if lower.endswith(".csv") or lower.endswith(".txt") or lower.endswith(".tsv"):
        last_err = None
        for enc in ["utf-8-sig", "utf-8", "cp1252", "latin1"]:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding=enc)
                if enc not in ("utf-8-sig", "utf-8"):
                    notes.append(f"File was not UTF-8; decoded as {enc}")
                return df, notes
            except Exception as e:  # try next encoding
                last_err = e
        raise ValueError(f"Could not read this CSV: {last_err}")
    return pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet), notes


def read_tabular_path(path: str, sheet=0) -> tuple:
    with open(path, "rb") as f:
        return read_tabular(os.path.basename(path), f.read(), sheet)

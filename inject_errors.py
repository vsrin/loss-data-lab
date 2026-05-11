#!/usr/bin/env python3
"""
inject_errors.py  —  Loss Transaction Dataset Error Injector (core logic)
-------------------------------------------------------------------------
Call generate(seed, rates) to inject errors into the clean workbook and
receive a dirty DataFrame plus a manifest of every change made.

Can also be run directly from the terminal:
    python3 inject_errors.py
"""

import csv
import os
import random
import warnings
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Defaults ───────────────────────────────────────────────────────────────────

INPUT_FILE = Path(__file__).parent / "060_Loss_Development HW3.xlsx"

DEFAULT_RATES = {
    "blank_claim_id":          0.010,
    "blank_transaction_date":  0.010,
    "mixed_date_format":       0.025,
    "misspell_transaction":    0.025,
    "wrong_capitalization":    0.015,
    "missing_negative":        0.050,
    "logical_date_violation":  0.005,
}

MISSPELLINGS = {
    "Reserve Change": ["Reseve Change", "Reserve Cahnge", "Reserver Change", "Rserve Change"],
    "Paid Loss":      ["Piad Loss",     "Paid Lsos",      "Paid  Loss",      "Paied Loss"],
}

CAPS_VARIANTS = {
    "Reserve Change": ["reserve change", "RESERVE CHANGE", "Reserve change", "reserve Change"],
    "Paid Loss":      ["paid loss",      "PAID LOSS",      "Paid loss"],
}

ALT_DATE_FORMATS = [
    lambda d: d.strftime("%m/%d/%Y"),
    lambda d: d.strftime("%m-%d-%Y"),
    lambda d: d.strftime("%B %d, %Y"),
    lambda d: d.strftime("%b %d %Y"),
    lambda d: d.strftime("%Y/%m/%d"),
    lambda d: d.strftime("%-m/%-d/%y"),
]

ERROR_LABELS = {
    "blank_claim_id":          "Blank Claim ID",
    "blank_transaction_date":  "Blank Transaction Date",
    "mixed_date_format":       "Mixed Date Format",
    "misspell_transaction":    "Misspelled Transaction",
    "wrong_capitalization":    "Wrong Capitalization",
    "missing_negative":        "Missing Negative Sign",
    "logical_date_violation":  "Logical Date Violation",
}

# ── Core function ──────────────────────────────────────────────────────────────

def generate(seed: int = 42, rates: dict = None):
    """
    Inject errors into the clean dataset.

    Returns:
        dirty_df  (pd.DataFrame) — corrupted data ready to write to Excel
        manifest  (pd.DataFrame) — every change, keyed by excel_row + column
    """
    if rates is None:
        rates = DEFAULT_RATES

    random.seed(seed)
    np.random.seed(seed)

    df_clean = pd.read_excel(
        INPUT_FILE,
        header=2,
        parse_dates=["Accident Date", "Transaction Date"],
    )
    df = df_clean.copy()

    changes         = []
    corrupted_cells = set()

    def log(row_idx, col, original, injected, error_type):
        changes.append({
            "excel_row":  row_idx + 4,
            "column":     col,
            "original":   str(original),
            "injected":   str(injected),
            "error_type": error_type,
            "error_label": ERROR_LABELS[error_type],
        })
        corrupted_cells.add((row_idx, col))

    def ok(row_idx, col):
        return (row_idx, col) not in corrupted_cells

    def sample_rows(rate, restrict_to=None):
        pool = list(df.index) if restrict_to is None else list(restrict_to)
        n    = max(1, round(len(df) * rate))
        return random.sample(pool, min(n, len(pool)))

    # 1. Blank Claim ID
    for r in sample_rows(rates["blank_claim_id"]):
        if not ok(r, "Claim ID"):
            continue
        log(r, "Claim ID", df.at[r, "Claim ID"], "", "blank_claim_id")
        df.at[r, "Claim ID"] = None

    # 2. Blank Transaction Date
    for r in sample_rows(rates["blank_transaction_date"]):
        if not ok(r, "Transaction Date"):
            continue
        orig = df.at[r, "Transaction Date"]
        log(r, "Transaction Date", orig.date() if pd.notna(orig) else "", "", "blank_transaction_date")
        df.at[r, "Transaction Date"] = None

    # 3. Mixed date format (Transaction Date written as a non-standard string)
    for r in sample_rows(rates["mixed_date_format"]):
        if not ok(r, "Transaction Date"):
            continue
        orig = df.at[r, "Transaction Date"]
        if pd.isna(orig):
            continue
        injected = random.choice(ALT_DATE_FORMATS)(orig)
        log(r, "Transaction Date", orig.date(), injected, "mixed_date_format")
        df.at[r, "Transaction Date"] = injected

    # 4. Misspelled Transaction
    for r in sample_rows(rates["misspell_transaction"]):
        if not ok(r, "Transaction"):
            continue
        orig = df.at[r, "Transaction"]
        if orig not in MISSPELLINGS:
            continue
        injected = random.choice(MISSPELLINGS[orig])
        log(r, "Transaction", orig, injected, "misspell_transaction")
        df.at[r, "Transaction"] = injected

    # 5. Wrong capitalization
    for r in sample_rows(rates["wrong_capitalization"]):
        if not ok(r, "Transaction"):
            continue
        orig = df.at[r, "Transaction"]
        if orig not in CAPS_VARIANTS:
            continue
        injected = random.choice(CAPS_VARIANTS[orig])
        log(r, "Transaction", orig, injected, "wrong_capitalization")
        df.at[r, "Transaction"] = injected

    # 6. Missing negative sign on reserve takedowns
    neg_rows = df[(df["Transaction"] == "Reserve Change") & (df["Amount"] < 0)].index.tolist()
    n_flip   = max(1, round(len(neg_rows) * rates["missing_negative"]))
    for r in random.sample(neg_rows, min(n_flip, len(neg_rows))):
        if not ok(r, "Amount"):
            continue
        orig = df.at[r, "Amount"]
        log(r, "Amount", orig, abs(orig), "missing_negative")
        df.at[r, "Amount"] = abs(orig)

    # 7. Logical date violation (Transaction Date before Accident Date)
    for r in sample_rows(rates["logical_date_violation"]):
        if not ok(r, "Transaction Date"):
            continue
        acc  = df.at[r, "Accident Date"]
        orig = df.at[r, "Transaction Date"]
        if pd.isna(acc) or pd.isna(orig):
            continue
        injected = acc - timedelta(days=random.randint(1, 30))
        log(r, "Transaction Date", orig.date(), injected.date(), "logical_date_violation")
        df.at[r, "Transaction Date"] = injected

    # Convert date columns to object so mixed datetime/string cells survive Excel write
    df["Accident Date"]    = df["Accident Date"].astype(object)
    df["Transaction Date"] = df["Transaction Date"].astype(object)

    manifest = pd.DataFrame(changes).sort_values("excel_row").reset_index(drop=True)
    return df, manifest


# ── CLI entry point ────────────────────────────────────────────────────────────

def main():
    seed = int(os.environ.get("RANDOM_SEED", "42"))
    dirty_df, manifest = generate(seed)

    output_dirty    = Path(__file__).parent / "Loss_Transactions_DIRTY.xlsx"
    output_manifest = Path(__file__).parent / "error_manifest.csv"

    with pd.ExcelWriter(output_dirty, engine="openpyxl",
                        date_format="YYYY-MM-DD", datetime_format="YYYY-MM-DD") as writer:
        dirty_df.to_excel(writer, index=False, sheet_name="Loss Transactions")

    manifest.to_csv(output_manifest, index=False)

    by_type = manifest.groupby("error_label").size()
    print(f"\nSeed: {seed}")
    print(f"Clean rows:      {2279:,}")
    print(f"Errors injected: {len(manifest):,}  ({len(manifest)/2279*100:.1f}% of rows)\n")
    for label, n in by_type.items():
        print(f"  {label:<30} {n:>4}")
    print(f"\nDirty workbook  →  {output_dirty}")
    print(f"Answer key      →  {output_manifest}")


if __name__ == "__main__":
    main()

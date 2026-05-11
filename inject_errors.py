#!/usr/bin/env python3
"""
inject_errors.py  —  Loss Transaction Dataset Error Injector
------------------------------------------------------------
Reads a clean loss-transaction workbook, injects deliberate data-quality
errors at configurable rates, and produces two output files:

  Loss_Transactions_DIRTY.xlsx  — give this to students
  error_manifest.csv            — keep as the grading answer key

Each row of the manifest records: Excel row number, column, original value,
injected value, and error type — so grading is objective and automatic.

Usage:
    python3 inject_errors.py

Requirements:
    pip install pandas openpyxl
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

# ── Configuration ──────────────────────────────────────────────────────────────

RANDOM_SEED     = int(os.environ.get("RANDOM_SEED", "42"))  # override via env var or GitHub Actions input
INPUT_FILE      = "060_Loss_Development HW3.xlsx"
OUTPUT_DIRTY    = "Loss_Transactions_DIRTY.xlsx"
OUTPUT_MANIFEST = "error_manifest.csv"

# Fraction of rows to corrupt per error type.
# Total injected errors will be roughly 8–12% of the 2,279 rows.
RATES = {
    "blank_claim_id":          0.010,  # ~23 rows  — missing Claim ID
    "blank_transaction_date":  0.010,  # ~23 rows  — missing Transaction Date
    "mixed_date_format":       0.025,  # ~57 rows  — Transaction Date as a non-standard text string
    "misspell_transaction":    0.025,  # ~57 rows  — typo in the Transaction field
    "wrong_capitalization":    0.015,  # ~34 rows  — wrong case in the Transaction field
    "missing_negative":        0.050,  # ~18 rows  — reserve takedowns that lost their minus sign
    "logical_date_violation":  0.005,  # ~11 rows  — Transaction Date earlier than Accident Date
}

# Typo variants for each transaction type
MISSPELLINGS = {
    "Reserve Change": ["Reseve Change", "Reserve Cahnge", "Reserver Change", "Rserve Change"],
    "Paid Loss":      ["Piad Loss",     "Paid Lsos",      "Paid  Loss",      "Paied Loss"],
}

# Capitalization variants
CAPS_VARIANTS = {
    "Reserve Change": ["reserve change", "RESERVE CHANGE", "Reserve change", "reserve Change"],
    "Paid Loss":      ["paid loss",      "PAID LOSS",      "Paid loss"],
}

# Non-standard date string formats (applied to Transaction Date)
ALT_DATE_FORMATS = [
    lambda d: d.strftime("%m/%d/%Y"),   # 01/05/2020  (ambiguous with day/month swap)
    lambda d: d.strftime("%m-%d-%Y"),   # 01-05-2020
    lambda d: d.strftime("%B %d, %Y"),  # January 05, 2020
    lambda d: d.strftime("%b %d %Y"),   # Jan 05 2020
    lambda d: d.strftime("%Y/%m/%d"),   # 2020/01/05
    lambda d: d.strftime("%-m/%-d/%y"), # 1/5/20  (two-digit year, no zero-padding)
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def pick(lst):
    """Return a random element from a list."""
    return random.choice(lst)


def sample_rows(df, rate, restrict_to=None):
    """
    Return a list of row indices to corrupt at the given rate.
    If restrict_to is provided, sample only from those indices.
    """
    pool = list(df.index) if restrict_to is None else list(restrict_to)
    n    = max(1, round(len(df) * rate))
    return random.sample(pool, min(n, len(pool)))


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # Read the clean dataset (header is on row 3; rows 1–2 are blank)
    df_clean = pd.read_excel(
        INPUT_FILE,
        header=2,
        parse_dates=["Accident Date", "Transaction Date"],
    )
    df = df_clean.copy()

    manifest        = []   # every change is logged here
    corrupted_cells = set()  # (row_index, column) — prevents double-corrupting a cell

    def log(row_idx, col, original, injected, error_type):
        manifest.append({
            "excel_row":  row_idx + 4,   # rows 1–2 blank, row 3 header → data starts at row 4
            "row_index":  row_idx,
            "column":     col,
            "original":   original,
            "injected":   injected,
            "error_type": error_type,
        })
        corrupted_cells.add((row_idx, col))

    def available(row_idx, col):
        """True if this cell has not already been corrupted."""
        return (row_idx, col) not in corrupted_cells

    # ── 1. Blank Claim ID ──────────────────────────────────────────────────────
    for r in sample_rows(df, RATES["blank_claim_id"]):
        if not available(r, "Claim ID"):
            continue
        orig = df.at[r, "Claim ID"]
        df.at[r, "Claim ID"] = None
        log(r, "Claim ID", orig, "", "blank_claim_id")

    # ── 2. Blank Transaction Date ──────────────────────────────────────────────
    for r in sample_rows(df, RATES["blank_transaction_date"]):
        if not available(r, "Transaction Date"):
            continue
        orig = df.at[r, "Transaction Date"]
        df.at[r, "Transaction Date"] = None
        log(r, "Transaction Date", str(orig.date()) if pd.notna(orig) else "", "", "blank_transaction_date")

    # ── 3. Mixed date format ───────────────────────────────────────────────────
    # Overwrite Transaction Date with a non-standard text string so students
    # must detect and normalize the format inconsistency.
    for r in sample_rows(df, RATES["mixed_date_format"]):
        if not available(r, "Transaction Date"):
            continue
        orig = df.at[r, "Transaction Date"]
        if pd.isna(orig):
            continue
        fmt_fn   = pick(ALT_DATE_FORMATS)
        injected = fmt_fn(orig)
        df.at[r, "Transaction Date"] = injected
        log(r, "Transaction Date", str(orig.date()), injected, "mixed_date_format")

    # ── 4. Misspelled Transaction ──────────────────────────────────────────────
    for r in sample_rows(df, RATES["misspell_transaction"]):
        if not available(r, "Transaction"):
            continue
        orig = df.at[r, "Transaction"]
        if orig not in MISSPELLINGS:
            continue
        injected = pick(MISSPELLINGS[orig])
        df.at[r, "Transaction"] = injected
        log(r, "Transaction", orig, injected, "misspell_transaction")

    # ── 5. Wrong capitalization ────────────────────────────────────────────────
    for r in sample_rows(df, RATES["wrong_capitalization"]):
        if not available(r, "Transaction"):
            continue
        orig = df.at[r, "Transaction"]
        if orig not in CAPS_VARIANTS:
            continue
        injected = pick(CAPS_VARIANTS[orig])
        df.at[r, "Transaction"] = injected
        log(r, "Transaction", orig, injected, "wrong_capitalization")

    # ── 6. Missing negative sign ───────────────────────────────────────────────
    # Reserve takedowns should be negative. Flip the sign to make them positive.
    neg_reserve_rows = df[
        (df["Transaction"] == "Reserve Change") & (df["Amount"] < 0)
    ].index.tolist()
    n_flip    = max(1, round(len(neg_reserve_rows) * RATES["missing_negative"]))
    flip_rows = random.sample(neg_reserve_rows, min(n_flip, len(neg_reserve_rows)))
    for r in flip_rows:
        if not available(r, "Amount"):
            continue
        orig     = df.at[r, "Amount"]
        injected = abs(orig)
        df.at[r, "Amount"] = injected
        log(r, "Amount", orig, injected, "missing_negative")

    # ── 7. Logical date violation ──────────────────────────────────────────────
    # Transaction Date is set to a date before Accident Date, which is
    # impossible in claims data. These violations require domain knowledge
    # to detect and are not caught by format or spelling checks.
    for r in sample_rows(df, RATES["logical_date_violation"]):
        if not available(r, "Transaction Date"):
            continue
        acc_date = df.at[r, "Accident Date"]
        orig     = df.at[r, "Transaction Date"]
        if pd.isna(acc_date) or pd.isna(orig):
            continue
        days_back = random.randint(1, 30)
        injected  = acc_date - timedelta(days=days_back)
        df.at[r, "Transaction Date"] = injected
        log(
            r, "Transaction Date",
            str(orig.date()) if hasattr(orig, "date") else str(orig),
            str(injected.date()),
            "logical_date_violation",
        )

    # ── Write dirty Excel file ─────────────────────────────────────────────────
    # Convert date columns to object so mixed datetime / string cells are
    # preserved correctly by openpyxl (string cells write as text, datetime
    # cells write as formatted dates).
    df["Accident Date"]    = df["Accident Date"].astype(object)
    df["Transaction Date"] = df["Transaction Date"].astype(object)

    with pd.ExcelWriter(
        OUTPUT_DIRTY,
        engine="openpyxl",
        date_format="YYYY-MM-DD",
        datetime_format="YYYY-MM-DD",
    ) as writer:
        df.to_excel(writer, index=False, sheet_name="Loss Transactions")

    # ── Write manifest (answer key) ────────────────────────────────────────────
    fieldnames = ["excel_row", "row_index", "column", "original", "injected", "error_type"]
    with open(OUTPUT_MANIFEST, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(sorted(manifest, key=lambda x: x["row_index"]))

    # ── Print summary ──────────────────────────────────────────────────────────
    by_type = {}
    for m in manifest:
        by_type[m["error_type"]] = by_type.get(m["error_type"], 0) + 1

    print(f"\nClean rows:      {len(df_clean):,}")
    print(f"Errors injected: {len(manifest):,}  ({len(manifest)/len(df_clean)*100:.1f}% of rows)")
    print()
    print(f"{'Error type':<30} {'Count':>6}")
    print("-" * 38)
    for t, n in sorted(by_type.items()):
        print(f"  {t:<28} {n:>6}")
    print()
    print(f"Dirty workbook  →  {OUTPUT_DIRTY}")
    print(f"Answer key CSV  →  {OUTPUT_MANIFEST}")
    print()
    print("Tip: change RANDOM_SEED at the top of this file each semester")
    print("     to produce a fresh error distribution from the same clean source.")


if __name__ == "__main__":
    main()

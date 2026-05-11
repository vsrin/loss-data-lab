import io
import random

import pandas as pd
import streamlit as st

from inject_errors import DEFAULT_RATES, generate, _apply_date_format

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Loss Data Lab",
    page_icon="",
    layout="wide",
)

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## Loss Data Lab")
    st.caption("Data Quality Classroom Tool")
    st.divider()

    st.markdown("**About**")
    st.markdown(
        "Takes a clean insurance loss transaction dataset — "
        "**2,279 transactions**, **400 claims**, 2020–2025 — "
        "and injects realistic data quality errors for classroom exercises. "
        "The answer key makes grading objective."
    )
    st.divider()

    st.markdown("**How to Use**")
    st.markdown(
        "1. Enter or randomize a **seed number**\n"
        "2. Click **Generate Dataset**\n"
        "3. Download **Dirty Dataset** — give to students\n"
        "4. Download **Answer Key** — keep for grading\n"
        "5. Change the seed each semester for a fresh version"
    )

# ── Error reference table data ─────────────────────────────────────────────────

ERROR_REF = pd.DataFrame({
    "Error Type": [
        "Blank Claim ID",
        "Blank Transaction Date",
        "Mixed Date Format",
        "Misspelled Transaction",
        "Wrong Capitalization",
        "Missing Negative Sign",
        "Logical Date Violation",
    ],
    "Example": [
        "Cell is empty",
        "Cell is empty",
        '"Jan 05 2020" vs "2020-01-05"',
        '"Reseve Change",  "Piad Loss"',
        '"reserve change",  "PAID LOSS"',
        "Reserve takedown shown as positive",
        "Transaction Date before Accident Date",
    ],
    "Level": ["Easy", "Easy", "Easy", "Easy", "Medium", "Medium", "Hard"],
    "Why It Matters": [
        "Orphaned records that cannot be joined to other tables",
        "Breaks time-series and development period calculations",
        "Silent parsing errors — some tools read wrong date, others fail",
        "Breaks group-by counts and aggregations",
        "Looks correct to the eye; breaks case-sensitive filters",
        "Inflates incurred loss totals; requires domain knowledge to spot",
        "Impossible in claims data; AI tools sometimes miss it",
    ],
})

# ── Main: two-column layout ────────────────────────────────────────────────────

left_col, right_col = st.columns([6, 4], gap="large")

# ── Left: error reference ──────────────────────────────────────────────────────

with left_col:
    st.markdown("#### Error Reference")
    st.dataframe(ERROR_REF, hide_index=True, use_container_width=True, height=283)
    st.caption(
        "The Logical Date Violation is the most valuable for class discussion. "
        "It requires domain knowledge, not just format checking, and reliably "
        "reveals the limits of AI-assisted data cleaning."
    )

# ── Right: generator ───────────────────────────────────────────────────────────

with right_col:
    st.markdown("#### Generate Dataset")

    seed_col, btn_col = st.columns([3, 1])

    with seed_col:
        seed = st.number_input(
            "Seed Number",
            min_value=1,
            max_value=99999,
            value=st.session_state.get("seed", 42),
            step=1,
            help="Same seed = same errors every time. Change each semester for a fresh version.",
        )

    with btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Shuffle", use_container_width=True):
            st.session_state["seed"] = random.randint(100, 99999)
            st.rerun()

    if "seed" in st.session_state:
        seed = st.session_state["seed"]

    st.caption(f"Seed **{int(seed)}** — the same seed always reproduces the same errors.")

    st.markdown(" ")

    if st.button("Generate Dataset", type="primary", use_container_width=True,
                 icon=":material/play_arrow:"):
        with st.spinner("Injecting errors…"):
            dirty_df, manifest = generate(seed=int(seed), rates=DEFAULT_RATES)
        st.session_state["results"] = {
            "dirty_df": dirty_df,
            "manifest": manifest,
            "seed": int(seed),
        }
        st.rerun()

# ── Results (full width, below both columns) ───────────────────────────────────

if "results" in st.session_state:
    r = st.session_state["results"]
    manifest  = r["manifest"]
    dirty_df  = r["dirty_df"]
    used_seed = r["seed"]

    total    = len(manifest)
    pct      = total / 2279 * 100
    by_label = (
        manifest.groupby("error_label").size()
        .reset_index(name="Count")
        .rename(columns={"error_label": "Error Type"})
    )

    st.divider()
    st.markdown("#### Results")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Errors Injected", total)
    m2.metric("Rows Affected", f"{pct:.1f}%")
    m3.metric("Total Rows", "2,279")
    m4.metric("Seed Used", used_seed)

    res_left, res_right = st.columns([1, 1], gap="large")

    with res_left:
        st.dataframe(by_label, hide_index=True, use_container_width=True)

    with res_right:
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(
            excel_buf, engine="openpyxl",
            date_format="YYYY-MM-DD", datetime_format="YYYY-MM-DD",
        ) as writer:
            dirty_df.to_excel(writer, index=False, sheet_name="Loss Transactions", startrow=2)
            _apply_date_format(writer.sheets["Loss Transactions"])
        excel_buf.seek(0)

        st.download_button(
            "Download Dirty Dataset (.xlsx)",
            data=excel_buf,
            file_name=f"Loss_Transactions_DIRTY_seed{used_seed}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            icon=":material/download:",
            help="Distribute this file to students.",
        )

        csv_buf = io.StringIO()
        manifest.to_csv(csv_buf, index=False)

        st.download_button(
            "Download Answer Key (.csv)",
            data=csv_buf.getvalue().encode(),
            file_name=f"error_manifest_seed{used_seed}.csv",
            mime="text/csv",
            use_container_width=True,
            icon=":material/key:",
            help="Keep this — records every injected error for grading.",
        )

        st.caption(f"Seed **{used_seed}** — use this number anytime to reproduce this exact version.")

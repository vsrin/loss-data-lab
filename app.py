import io
import random

import pandas as pd
import streamlit as st

from inject_errors import DEFAULT_RATES, ERROR_LABELS, generate

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Loss Data Lab",
    page_icon="📊",
    layout="centered",
)

# ── Header ─────────────────────────────────────────────────────────────────────

st.title("📊 Loss Data Lab")
st.markdown(
    "Generate a deliberately messy version of the loss transaction dataset "
    "for use in classroom data-cleaning exercises. "
    "Choose a seed, click **Generate**, and download your files."
)
st.divider()

# ── Seed input ─────────────────────────────────────────────────────────────────

col1, col2 = st.columns([3, 1])
with col1:
    seed = st.number_input(
        "Random seed",
        min_value=1,
        max_value=99999,
        value=42,
        step=1,
        help="Change this number each semester to produce a fresh error distribution. "
             "The same seed always produces the same errors, so you can reproduce any version.",
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🎲 Randomize", use_container_width=True):
        seed = random.randint(100, 99999)
        st.rerun()

# ── Advanced: error rate sliders ───────────────────────────────────────────────

with st.expander("⚙️ Adjust error rates (optional)"):
    st.markdown("Default rates work well for most classes. Adjust only if you want more or fewer of a specific error type.")
    rates = {}
    for key, label in ERROR_LABELS.items():
        rates[key] = st.slider(
            label,
            min_value=0.0,
            max_value=0.10,
            value=DEFAULT_RATES[key],
            step=0.005,
            format="%.1%%",
            key=key,
        )

# ── Generate ───────────────────────────────────────────────────────────────────

st.divider()

if st.button("⚡ Generate Dataset", type="primary", use_container_width=True):
    with st.spinner("Injecting errors…"):
        dirty_df, manifest = generate(seed=int(seed), rates=rates)

    total  = len(manifest)
    pct    = total / 2279 * 100
    by_label = manifest.groupby("error_label").size().reset_index(name="count")

    st.success(f"Done — **{total} errors** injected across {pct:.1f}% of rows.")
    st.dataframe(
        by_label.rename(columns={"error_label": "Error Type", "count": "Count"}),
        hide_index=True,
        use_container_width=True,
    )

    st.divider()
    st.markdown("### Download your files")
    dl1, dl2 = st.columns(2)

    # Dirty Excel
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl",
                        date_format="YYYY-MM-DD", datetime_format="YYYY-MM-DD") as writer:
        dirty_df.to_excel(writer, index=False, sheet_name="Loss Transactions")
    excel_buf.seek(0)

    with dl1:
        st.download_button(
            label="📥 Download Dirty Dataset",
            data=excel_buf,
            file_name=f"Loss_Transactions_DIRTY_seed{int(seed)}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="Give this file to students.",
        )

    # Manifest CSV
    csv_buf = io.StringIO()
    manifest.to_csv(csv_buf, index=False)

    with dl2:
        st.download_button(
            label="🔑 Download Answer Key",
            data=csv_buf.getvalue().encode(),
            file_name=f"error_manifest_seed{int(seed)}.csv",
            mime="text/csv",
            use_container_width=True,
            help="Keep this file — it records every injected error for grading.",
        )

    st.caption(
        f"Seed **{int(seed)}** · {total} errors · "
        "Use the same seed again anytime to reproduce this exact version."
    )

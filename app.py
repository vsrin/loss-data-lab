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

# ── Custom CSS ─────────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Hero banner */
.hero {
    background: linear-gradient(135deg, #2563EB 0%, #0EA5E9 100%);
    border-radius: 16px;
    padding: 2.5rem 2rem 2rem 2rem;
    color: white;
    margin-bottom: 2rem;
}
.hero h1 { color: white; font-size: 2.1rem; margin-bottom: 0.3rem; }
.hero p  { color: rgba(255,255,255,0.88); font-size: 1.05rem; margin: 0; }

/* Section cards */
.card {
    background: #EFF6FF;
    border-left: 4px solid #2563EB;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}
.card h3 { margin-top: 0; color: #1E3A8A; font-size: 1rem; }
.card p, .card li { font-size: 0.93rem; color: #374151; margin: 0.2rem 0; }

/* Step badges */
.step {
    display: inline-block;
    background: #2563EB;
    color: white;
    font-weight: 700;
    font-size: 0.8rem;
    border-radius: 50%;
    width: 1.5rem;
    height: 1.5rem;
    text-align: center;
    line-height: 1.5rem;
    margin-right: 0.5rem;
}

/* Error type table */
.err-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.err-table th {
    background: #2563EB; color: white;
    padding: 0.5rem 0.8rem; text-align: left;
}
.err-table td { padding: 0.45rem 0.8rem; border-bottom: 1px solid #DBEAFE; }
.err-table tr:nth-child(even) td { background: #EFF6FF; }
.badge-easy   { background:#D1FAE5; color:#065F46; border-radius:4px; padding:2px 7px; font-size:0.78rem; }
.badge-medium { background:#FEF3C7; color:#92400E; border-radius:4px; padding:2px 7px; font-size:0.78rem; }
.badge-hard   { background:#FEE2E2; color:#991B1B; border-radius:4px; padding:2px 7px; font-size:0.78rem; }

/* Section header rule */
.section-title {
    font-size: 1.1rem; font-weight: 700;
    color: #1E3A8A; margin: 1.5rem 0 0.8rem 0;
    border-bottom: 2px solid #BFDBFE; padding-bottom: 0.3rem;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
    <h1>📊 Loss Data Lab</h1>
    <p>
        A classroom tool for teaching data quality and AI-assisted data cleaning.
        Generate a deliberately messy insurance dataset, hand it to your students,
        and use the answer key to grade their corrections.
    </p>
</div>
""", unsafe_allow_html=True)

# ── About ──────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">About this tool</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    st.markdown("""
    <div class="card">
        <h3>🎯 What it does</h3>
        <p>
            Takes a clean insurance loss transaction dataset (2,279 real-world transactions
            across 400 claims, 2020–2025) and injects deliberate data quality errors —
            the same kinds of problems that appear in production systems every day.
        </p>
        <p style="margin-top:0.6rem;">
            Students use AI tools (ChatGPT, Claude, Python/pandas, OpenRefine) to find
            and fix the errors. The <strong>answer key</strong> records every injected
            error so grading is objective.
        </p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="card">
        <h3>💡 Why this approach</h3>
        <p>
            Starting from a <em>known</em> clean dataset lets students validate their
            own corrections against a ground truth — something you can't do with
            naturally dirty data.
        </p>
        <p style="margin-top:0.6rem;">
            Errors are scattered throughout the existing rows, not appended at the
            bottom, so students must actually audit the data rather than simply
            filtering by row position.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── How to use ─────────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">How to use this tool</div>', unsafe_allow_html=True)

st.markdown("""
<div class="card">
    <p><span class="step">1</span><strong>Pick a seed number</strong> below — any number works.
       The same seed always produces the same errors, so you can reproduce any version exactly.</p>
    <p><span class="step">2</span><strong>Click Generate.</strong>
       The tool injects errors and shows you a summary of what was changed.</p>
    <p><span class="step">3</span><strong>Download the Dirty Dataset</strong> and distribute it to students.</p>
    <p><span class="step">4</span><strong>Download the Answer Key</strong> (CSV) and keep it for grading.
       It lists every injected error with the Excel row, column, original value, and injected value.</p>
    <p><span class="step">5</span><strong>Next semester</strong>, change the seed number and repeat.
       Fresh error distribution, same clean source — no manual work needed.</p>
</div>
""", unsafe_allow_html=True)

# ── Error type guide ───────────────────────────────────────────────────────────

with st.expander("📖 Error type reference — what students will encounter"):
    st.markdown("""
    <table class="err-table">
        <tr>
            <th>Error Type</th>
            <th>Example</th>
            <th>Difficulty</th>
            <th>Why it matters</th>
        </tr>
        <tr>
            <td><strong>Blank Claim ID</strong></td>
            <td>Cell is empty</td>
            <td><span class="badge-easy">Easy</span></td>
            <td>Orphaned records that can't be joined to other tables</td>
        </tr>
        <tr>
            <td><strong>Blank Transaction Date</strong></td>
            <td>Cell is empty</td>
            <td><span class="badge-easy">Easy</span></td>
            <td>Breaks any time-series or development period calculation</td>
        </tr>
        <tr>
            <td><strong>Mixed Date Format</strong></td>
            <td>"Jan 05 2020" vs "2020-01-05"</td>
            <td><span class="badge-easy">Easy</span></td>
            <td>Silent parsing errors — some tools read wrong date, others fail</td>
        </tr>
        <tr>
            <td><strong>Misspelled Transaction</strong></td>
            <td>"Reseve Change", "Piad Loss"</td>
            <td><span class="badge-easy">Easy</span></td>
            <td>Causes incorrect group-by counts and aggregation errors</td>
        </tr>
        <tr>
            <td><strong>Wrong Capitalization</strong></td>
            <td>"reserve change", "PAID LOSS"</td>
            <td><span class="badge-medium">Medium</span></td>
            <td>Looks correct to the eye; breaks case-sensitive filters</td>
        </tr>
        <tr>
            <td><strong>Missing Negative Sign</strong></td>
            <td>Reserve takedown shown as positive</td>
            <td><span class="badge-medium">Medium</span></td>
            <td>Inflates total incurred loss figures; requires domain knowledge to spot</td>
        </tr>
        <tr>
            <td><strong>Logical Date Violation</strong></td>
            <td>Transaction Date before Accident Date</td>
            <td><span class="badge-hard">Hard</span></td>
            <td>Impossible in claims data; AI tools sometimes miss it — good class discussion</td>
        </tr>
    </table>
    <p style="font-size:0.82rem; color:#6B7280; margin-top:0.8rem;">
        The logical date violation is intentionally the hardest. It requires domain knowledge,
        not just format checks, and is a reliable way to start a conversation about
        what AI tools can and cannot be trusted to catch on their own.
    </p>
    """, unsafe_allow_html=True)

# ── Generator ──────────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">Generate your dataset</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    seed = st.number_input(
        "Seed number",
        min_value=1,
        max_value=99999,
        value=42,
        step=1,
        help="Change this each semester. Same seed = same errors, so you can always reproduce a prior version.",
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🎲 Randomize", use_container_width=True):
        st.session_state["seed"] = random.randint(100, 99999)
        st.rerun()

if "seed" in st.session_state:
    seed = st.session_state["seed"]

with st.expander("⚙️ Advanced: adjust error rates"):
    st.caption("Default rates are calibrated for a 50-minute class exercise. Adjust only if you want more or fewer of a specific error type.")
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
else:
    rates = DEFAULT_RATES

st.markdown("<br>", unsafe_allow_html=True)

if st.button("⚡  Generate Dataset", type="primary", use_container_width=True):
    with st.spinner("Injecting errors into the dataset…"):
        dirty_df, manifest = generate(seed=int(seed), rates=rates)

    total    = len(manifest)
    pct      = total / 2279 * 100
    by_label = manifest.groupby("error_label").size().reset_index(name="Count")
    by_label = by_label.rename(columns={"error_label": "Error Type"})

    st.success(f"✅  Ready — **{total} errors** injected across {pct:.1f}% of rows  |  Seed: **{int(seed)}**")
    st.dataframe(by_label, hide_index=True, use_container_width=True)

    st.markdown("#### Download your files")
    dl1, dl2 = st.columns(2)

    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl",
                        date_format="YYYY-MM-DD", datetime_format="YYYY-MM-DD") as writer:
        dirty_df.to_excel(writer, index=False, sheet_name="Loss Transactions")
    excel_buf.seek(0)

    with dl1:
        st.download_button(
            label="📥  Dirty Dataset (.xlsx)",
            data=excel_buf,
            file_name=f"Loss_Transactions_DIRTY_seed{int(seed)}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="Distribute this file to students.",
        )

    csv_buf = io.StringIO()
    manifest.to_csv(csv_buf, index=False)

    with dl2:
        st.download_button(
            label="🔑  Answer Key (.csv)",
            data=csv_buf.getvalue().encode(),
            file_name=f"error_manifest_seed{int(seed)}.csv",
            mime="text/csv",
            use_container_width=True,
            help="Keep this file — it records every injected error for grading.",
        )

    st.caption(
        f"💾  Use seed **{int(seed)}** again at any time to reproduce this exact version of the dataset."
    )

# ── Footer ─────────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "Loss Data Lab · Built for classroom use · "
    "Source dataset: 2,279 loss transactions, 400 claims, 2020–2025"
)

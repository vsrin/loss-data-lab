import io
import random

import pandas as pd
import streamlit as st

from inject_errors import DEFAULT_RATES, ERROR_LABELS, generate

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Loss Data Lab",
    page_icon="",
    layout="wide",
)

# ── Font Awesome + CSS ─────────────────────────────────────────────────────────

st.markdown("""
<link rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">

<style>
/* ── Global resets ── */
section[data-testid="stMain"] > div   { padding-top: 0.6rem !important; }
section[data-testid="stSidebar"] > div { padding-top: 0.8rem !important; }
.block-container { padding-top: 0.6rem !important; padding-bottom: 0.5rem !important; }
div[data-testid="stVerticalBlock"] { gap: 0.4rem !important; }

/* ── Sidebar brand ── */
.brand {
    display: flex; align-items: center; gap: 0.6rem;
    margin-bottom: 0.6rem;
}
.brand-icon {
    background: #2563EB; color: white;
    border-radius: 8px; width: 2rem; height: 2rem;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
}
.brand-title { font-size: 1.05rem; font-weight: 700; color: #1E293B; line-height: 1.2; }
.brand-sub   { font-size: 0.72rem; color: #64748B; }

/* ── Sidebar sections ── */
.sb-section { margin-bottom: 0.8rem; }
.sb-heading {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #94A3B8; margin-bottom: 0.4rem;
}
.sb-body { font-size: 0.82rem; color: #374151; line-height: 1.55; }

/* ── Steps ── */
.step-row { display: flex; align-items: flex-start; gap: 0.55rem; margin-bottom: 0.35rem; }
.step-num {
    background: #2563EB; color: white; font-size: 0.65rem; font-weight: 700;
    border-radius: 50%; width: 1.2rem; height: 1.2rem; min-width: 1.2rem;
    display: flex; align-items: center; justify-content: center; margin-top: 1px;
}
.step-text { font-size: 0.82rem; color: #374151; line-height: 1.45; }

/* ── Error reference table ── */
.err-tbl { width: 100%; border-collapse: collapse; font-size: 0.78rem; margin-top: 0.3rem; }
.err-tbl th {
    background: #1E3A8A; color: white;
    padding: 0.3rem 0.5rem; text-align: left; font-weight: 600;
}
.err-tbl td { padding: 0.28rem 0.5rem; border-bottom: 1px solid #DBEAFE; color: #374151; }
.err-tbl tr:nth-child(even) td { background: #F0F7FF; }
.lv-e { color: #059669; font-weight: 600; font-size: 0.72rem; }
.lv-m { color: #D97706; font-weight: 600; font-size: 0.72rem; }
.lv-h { color: #DC2626; font-weight: 600; font-size: 0.72rem; }

/* ── Main panel ── */
.panel-header {
    display: flex; align-items: center; gap: 0.5rem;
    margin-bottom: 0.5rem;
}
.panel-icon {
    background: #EFF6FF; color: #2563EB;
    border-radius: 6px; width: 1.8rem; height: 1.8rem;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem;
}
.panel-title { font-size: 1.1rem; font-weight: 700; color: #1E293B; }

/* ── Result summary cards ── */
.result-cards { display: flex; gap: 0.6rem; margin-bottom: 0.6rem; flex-wrap: wrap; }
.r-card {
    flex: 1; min-width: 130px;
    background: #EFF6FF; border: 1px solid #BFDBFE;
    border-radius: 8px; padding: 0.5rem 0.8rem;
    text-align: center;
}
.r-card-num { font-size: 1.4rem; font-weight: 700; color: #2563EB; line-height: 1.2; }
.r-card-lbl { font-size: 0.72rem; color: #64748B; }

hr.sb-rule { border: none; border-top: 1px solid #E2E8F0; margin: 0.6rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:

    # Brand
    st.markdown("""
    <div class="brand">
        <div class="brand-icon"><i class="fa-solid fa-database"></i></div>
        <div>
            <div class="brand-title">Loss Data Lab</div>
            <div class="brand-sub">Data Quality Classroom Tool</div>
        </div>
    </div>
    <hr class="sb-rule">
    """, unsafe_allow_html=True)

    # About
    st.markdown("""
    <div class="sb-section">
        <div class="sb-heading"><i class="fa-solid fa-circle-info" style="margin-right:4px"></i>About</div>
        <div class="sb-body">
            Injects deliberate data quality errors into a clean insurance loss
            transaction dataset — <strong>2,279 transactions</strong> across
            <strong>400 claims</strong> (2020–2025). Students use AI tools to
            detect and fix the errors; the answer key enables objective grading.
        </div>
    </div>
    <hr class="sb-rule">
    """, unsafe_allow_html=True)

    # How to use
    st.markdown("""
    <div class="sb-section">
        <div class="sb-heading"><i class="fa-solid fa-list-ol" style="margin-right:4px"></i>How to Use</div>
        <div class="step-row"><div class="step-num">1</div>
            <div class="step-text">Enter or randomize a <strong>seed number</strong></div></div>
        <div class="step-row"><div class="step-num">2</div>
            <div class="step-text">Click <strong>Generate Dataset</strong></div></div>
        <div class="step-row"><div class="step-num">3</div>
            <div class="step-text">Download the <strong>Dirty Dataset</strong> — give to students</div></div>
        <div class="step-row"><div class="step-num">4</div>
            <div class="step-text">Download the <strong>Answer Key</strong> — keep for grading</div></div>
        <div class="step-row"><div class="step-num">5</div>
            <div class="step-text">Change the seed each semester for a fresh version</div></div>
    </div>
    <hr class="sb-rule">
    """, unsafe_allow_html=True)

    # Error reference
    st.markdown("""
    <div class="sb-section">
        <div class="sb-heading"><i class="fa-solid fa-triangle-exclamation" style="margin-right:4px"></i>Error Reference</div>
        <table class="err-tbl">
            <tr><th>Error Type</th><th>Level</th></tr>
            <tr><td>Blank Claim ID</td><td><span class="lv-e">Easy</span></td></tr>
            <tr><td>Blank Transaction Date</td><td><span class="lv-e">Easy</span></td></tr>
            <tr><td>Mixed Date Format</td><td><span class="lv-e">Easy</span></td></tr>
            <tr><td>Misspelled Transaction</td><td><span class="lv-e">Easy</span></td></tr>
            <tr><td>Wrong Capitalization</td><td><span class="lv-m">Medium</span></td></tr>
            <tr><td>Missing Negative Sign</td><td><span class="lv-m">Medium</span></td></tr>
            <tr><td>Logical Date Violation</td><td><span class="lv-h">Hard</span></td></tr>
        </table>
        <div class="sb-body" style="margin-top:0.45rem; font-size:0.74rem; color:#64748B;">
            Hard errors require domain knowledge and are not reliably caught by AI —
            useful for classroom discussion.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Main panel ─────────────────────────────────────────────────────────────────

st.markdown("""
<div class="panel-header">
    <div class="panel-icon"><i class="fa-solid fa-wand-magic-sparkles"></i></div>
    <div class="panel-title">Dataset Generator</div>
</div>
""", unsafe_allow_html=True)

# Seed row
c_seed, c_btn = st.columns([4, 1])
with c_seed:
    seed = st.number_input(
        "Seed number",
        min_value=1, max_value=99999,
        value=st.session_state.get("seed", 42),
        step=1,
        label_visibility="collapsed",
        help="Same seed = same errors every time. Change each semester for a fresh version.",
    )
with c_btn:
    if st.button("Shuffle", icon=":material/shuffle:", use_container_width=True):
        st.session_state["seed"] = random.randint(100, 99999)
        st.rerun()

st.caption(f"Seed **{int(seed)}** — the same seed always reproduces the same error distribution.")

# Advanced rates
with st.expander("Advanced — adjust error rates", icon=":material/tune:"):
    st.caption("Defaults are calibrated for a 50-minute exercise. Adjust only if needed.")
    rates = {}
    left, right = st.columns(2)
    items = list(ERROR_LABELS.items())
    for i, (key, label) in enumerate(items):
        col = left if i % 2 == 0 else right
        with col:
            rates[key] = st.slider(
                label, min_value=0.0, max_value=0.10,
                value=DEFAULT_RATES[key], step=0.005,
                format="%.1%%", key=key,
            )

st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

if st.button("Generate Dataset", type="primary", use_container_width=True,
             icon=":material/play_arrow:"):
    with st.spinner("Injecting errors…"):
        dirty_df, manifest = generate(seed=int(seed), rates=rates)

    total    = len(manifest)
    pct      = total / 2279 * 100
    by_label = manifest.groupby("error_label").size().reset_index(name="Count")
    by_label = by_label.rename(columns={"error_label": "Error Type"})

    # Summary cards
    st.markdown(f"""
    <div class="result-cards">
        <div class="r-card">
            <div class="r-card-num">{total}</div>
            <div class="r-card-lbl">Errors Injected</div>
        </div>
        <div class="r-card">
            <div class="r-card-num">{pct:.1f}%</div>
            <div class="r-card-lbl">Rows Affected</div>
        </div>
        <div class="r-card">
            <div class="r-card-num">2,279</div>
            <div class="r-card-lbl">Total Rows</div>
        </div>
        <div class="r-card">
            <div class="r-card-num">{int(seed)}</div>
            <div class="r-card-lbl">Seed Used</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.dataframe(by_label, hide_index=True, use_container_width=True, height=284)

    # Downloads
    dl1, dl2 = st.columns(2)

    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl",
                        date_format="YYYY-MM-DD", datetime_format="YYYY-MM-DD") as writer:
        dirty_df.to_excel(writer, index=False, sheet_name="Loss Transactions")
    excel_buf.seek(0)

    with dl1:
        st.download_button(
            label="Dirty Dataset (.xlsx)",
            data=excel_buf,
            file_name=f"Loss_Transactions_DIRTY_seed{int(seed)}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            icon=":material/download:",
            help="Distribute this file to students.",
        )

    csv_buf = io.StringIO()
    manifest.to_csv(csv_buf, index=False)

    with dl2:
        st.download_button(
            label="Answer Key (.csv)",
            data=csv_buf.getvalue().encode(),
            file_name=f"error_manifest_seed{int(seed)}.csv",
            mime="text/csv",
            use_container_width=True,
            icon=":material/key:",
            help="Keep this — records every injected error for grading.",
        )

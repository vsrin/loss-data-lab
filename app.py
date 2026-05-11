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
/* Tighten Streamlit's default whitespace */
.main .block-container { padding-top: 1.2rem !important; padding-bottom: 0.5rem !important; }
[data-testid="stSidebar"] .block-container { padding-top: 0.8rem !important; }

/* Sidebar brand block */
.brand { display:flex; align-items:center; gap:0.55rem; margin-bottom:0.5rem; }
.brand-icon {
    background:#2563EB; color:white; border-radius:7px;
    width:2rem; height:2rem; display:flex; align-items:center;
    justify-content:center; font-size:0.95rem; flex-shrink:0;
}
.brand-name { font-size:1rem; font-weight:700; color:#1E293B; }
.brand-sub  { font-size:0.7rem; color:#64748B; }

/* Sidebar section headings */
.sb-head {
    font-size:0.65rem; font-weight:700; letter-spacing:0.09em;
    text-transform:uppercase; color:#94A3B8; margin:0.7rem 0 0.35rem;
}
.sb-body { font-size:0.8rem; color:#374151; line-height:1.5; }

/* Numbered steps */
.step-row { display:flex; align-items:flex-start; gap:0.5rem; margin-bottom:0.3rem; }
.step-num {
    background:#2563EB; color:white; font-size:0.62rem; font-weight:700;
    border-radius:50%; min-width:1.15rem; height:1.15rem;
    display:flex; align-items:center; justify-content:center; margin-top:2px;
}
.step-text { font-size:0.8rem; color:#374151; line-height:1.4; }

/* Sidebar rule */
hr.sb { border:none; border-top:1px solid #E2E8F0; margin:0.55rem 0; }

/* Section header in main */
.sec-head {
    display:flex; align-items:center; gap:0.45rem; margin-bottom:0.6rem;
    border-bottom:2px solid #DBEAFE; padding-bottom:0.35rem;
}
.sec-icon {
    background:#EFF6FF; color:#2563EB; border-radius:5px;
    width:1.6rem; height:1.6rem; display:flex; align-items:center;
    justify-content:center; font-size:0.8rem; flex-shrink:0;
}
.sec-title { font-size:0.95rem; font-weight:700; color:#1E293B; }

/* Error reference table */
.err-tbl { width:100%; border-collapse:collapse; font-size:0.82rem; }
.err-tbl th {
    background:#1E3A8A; color:white;
    padding:0.35rem 0.65rem; text-align:left; font-weight:600;
}
.err-tbl td { padding:0.32rem 0.65rem; border-bottom:1px solid #DBEAFE; vertical-align:top; }
.err-tbl tr:nth-child(even) td { background:#F0F7FF; }
.err-tbl td:first-child { font-weight:600; color:#1E293B; white-space:nowrap; }
.lv-e { color:#059669; font-weight:700; font-size:0.74rem; }
.lv-m { color:#D97706; font-weight:700; font-size:0.74rem; }
.lv-h { color:#DC2626; font-weight:700; font-size:0.74rem; }

/* Result summary cards */
.rcards { display:flex; gap:0.5rem; margin:0.5rem 0 0.7rem; }
.rc {
    flex:1; background:#EFF6FF; border:1px solid #BFDBFE;
    border-radius:8px; padding:0.45rem 0.7rem; text-align:center;
}
.rc-n { font-size:1.3rem; font-weight:700; color:#2563EB; line-height:1.2; }
.rc-l { font-size:0.68rem; color:#64748B; margin-top:1px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="brand">
        <div class="brand-icon"><i class="fa-solid fa-database"></i></div>
        <div>
            <div class="brand-name">Loss Data Lab</div>
            <div class="brand-sub">Data Quality Classroom Tool</div>
        </div>
    </div>
    <hr class="sb">

    <div class="sb-head"><i class="fa-solid fa-circle-info" style="margin-right:3px"></i>About</div>
    <div class="sb-body">
        Takes a clean insurance loss transaction dataset —
        <strong>2,279 transactions</strong>, <strong>400 claims</strong>, 2020–2025 —
        and injects realistic data quality errors for student exercises.
        The answer key makes grading objective.
    </div>
    <hr class="sb">

    <div class="sb-head"><i class="fa-solid fa-list-ol" style="margin-right:3px"></i>How to Use</div>
    <div class="step-row">
        <div class="step-num">1</div>
        <div class="step-text">Enter or randomize a <strong>seed number</strong></div>
    </div>
    <div class="step-row">
        <div class="step-num">2</div>
        <div class="step-text">Click <strong>Generate Dataset</strong></div>
    </div>
    <div class="step-row">
        <div class="step-num">3</div>
        <div class="step-text">Download <strong>Dirty Dataset</strong> — give to students</div>
    </div>
    <div class="step-row">
        <div class="step-num">4</div>
        <div class="step-text">Download <strong>Answer Key</strong> — keep for grading</div>
    </div>
    <div class="step-row">
        <div class="step-num">5</div>
        <div class="step-text">Change the seed each semester for a fresh version</div>
    </div>
    """, unsafe_allow_html=True)

# ── Main: two-column layout ────────────────────────────────────────────────────

left, right = st.columns([56, 44], gap="large")

# ── Left: Error reference ──────────────────────────────────────────────────────

with left:
    st.markdown("""
    <div class="sec-head">
        <div class="sec-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
        <div class="sec-title">Error Reference</div>
    </div>
    <table class="err-tbl">
        <tr>
            <th>Error Type</th>
            <th>Example</th>
            <th>Level</th>
            <th>Why It Matters</th>
        </tr>
        <tr>
            <td>Blank Claim ID</td>
            <td>Cell is empty</td>
            <td><span class="lv-e">Easy</span></td>
            <td>Orphaned records that cannot be joined to other tables</td>
        </tr>
        <tr>
            <td>Blank Transaction Date</td>
            <td>Cell is empty</td>
            <td><span class="lv-e">Easy</span></td>
            <td>Breaks time-series and development period calculations</td>
        </tr>
        <tr>
            <td>Mixed Date Format</td>
            <td>"Jan 05 2020" vs "2020-01-05"</td>
            <td><span class="lv-e">Easy</span></td>
            <td>Silent parsing errors — some tools read wrong date, others fail</td>
        </tr>
        <tr>
            <td>Misspelled Transaction</td>
            <td>"Reseve Change", "Piad Loss"</td>
            <td><span class="lv-e">Easy</span></td>
            <td>Breaks group-by counts and aggregation; easy for AI to catch</td>
        </tr>
        <tr>
            <td>Wrong Capitalization</td>
            <td>"reserve change", "PAID LOSS"</td>
            <td><span class="lv-m">Medium</span></td>
            <td>Looks correct to the eye; breaks case-sensitive filters</td>
        </tr>
        <tr>
            <td>Missing Negative Sign</td>
            <td>Reserve takedown shown as positive</td>
            <td><span class="lv-m">Medium</span></td>
            <td>Inflates incurred loss totals; requires domain knowledge to spot</td>
        </tr>
        <tr>
            <td>Logical Date Violation</td>
            <td>Transaction Date before Accident Date</td>
            <td><span class="lv-h">Hard</span></td>
            <td>Impossible in claims data; AI tools sometimes miss it</td>
        </tr>
    </table>
    <p style="font-size:0.74rem;color:#64748B;margin-top:0.5rem;line-height:1.4;">
        <i class="fa-solid fa-lightbulb" style="color:#D97706;margin-right:4px"></i>
        The logical date violation is the most valuable for class discussion —
        it requires domain knowledge, not just format checking, and reliably
        exposes the limits of AI-assisted data cleaning.
    </p>
    """, unsafe_allow_html=True)

# ── Right: Generator ───────────────────────────────────────────────────────────

with right:
    st.markdown("""
    <div class="sec-head">
        <div class="sec-icon"><i class="fa-solid fa-sliders"></i></div>
        <div class="sec-title">Dataset Generator</div>
    </div>
    """, unsafe_allow_html=True)

    # Seed row
    s1, s2 = st.columns([3, 1])
    with s1:
        seed = st.number_input(
            "Seed Number",
            min_value=1, max_value=99999,
            value=st.session_state.get("seed", 42),
            step=1,
            help="Same seed = same errors every time. Change each semester for a fresh version.",
        )
    with s2:
        st.markdown("<div style='height:1.82rem'></div>", unsafe_allow_html=True)
        if st.button("Shuffle", use_container_width=True,
                     icon=":material/shuffle:"):
            st.session_state["seed"] = random.randint(100, 99999)
            st.rerun()

    if "seed" in st.session_state:
        seed = st.session_state["seed"]

    st.caption(f"Seed **{int(seed)}** — same seed always reproduces the same errors.")

    # Advanced rates
    with st.expander("Advanced — adjust error rates", icon=":material/tune:"):
        st.caption("Defaults are calibrated for a 50-minute exercise.")
        rates = {}
        ra, rb = st.columns(2)
        for i, (key, label) in enumerate(ERROR_LABELS.items()):
            with (ra if i % 2 == 0 else rb):
                rates[key] = st.slider(
                    label, 0.0, 0.10, DEFAULT_RATES[key], 0.005,
                    format="%.1%%", key=key,
                )

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    generate_clicked = st.button(
        "Generate Dataset", type="primary", use_container_width=True,
        icon=":material/play_arrow:",
    )

# ── Results (full width, below both columns) ───────────────────────────────────

if generate_clicked:
    with st.spinner("Injecting errors…"):
        dirty_df, manifest = generate(seed=int(seed), rates=rates)

    total    = len(manifest)
    pct      = total / 2279 * 100
    by_label = (manifest.groupby("error_label").size()
                .reset_index(name="Count")
                .rename(columns={"error_label": "Error Type"}))

    st.divider()

    st.markdown(f"""
    <div class="rcards">
        <div class="rc"><div class="rc-n">{total}</div><div class="rc-l">Errors Injected</div></div>
        <div class="rc"><div class="rc-n">{pct:.1f}%</div><div class="rc-l">Rows Affected</div></div>
        <div class="rc"><div class="rc-n">2,279</div><div class="rc-l">Total Rows</div></div>
        <div class="rc"><div class="rc-n">{int(seed)}</div><div class="rc-l">Seed Used</div></div>
    </div>
    """, unsafe_allow_html=True)

    res_left, res_right = st.columns([1, 1])

    with res_left:
        st.dataframe(by_label, hide_index=True, use_container_width=True)

    with res_right:
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine="openpyxl",
                            date_format="YYYY-MM-DD",
                            datetime_format="YYYY-MM-DD") as writer:
            dirty_df.to_excel(writer, index=False, sheet_name="Loss Transactions")
        excel_buf.seek(0)

        st.download_button(
            "Dirty Dataset (.xlsx)",
            data=excel_buf,
            file_name=f"Loss_Transactions_DIRTY_seed{int(seed)}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            icon=":material/download:",
            help="Give this file to students.",
        )

        csv_buf = io.StringIO()
        manifest.to_csv(csv_buf, index=False)

        st.download_button(
            "Answer Key (.csv)",
            data=csv_buf.getvalue().encode(),
            file_name=f"error_manifest_seed{int(seed)}.csv",
            mime="text/csv",
            use_container_width=True,
            icon=":material/key:",
            help="Keep this — records every injected error for grading.",
        )

        st.caption(f"Seed **{int(seed)}** reproduces this exact version anytime.")

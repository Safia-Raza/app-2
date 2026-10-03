from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import streamlit as st

from workflow import run_payment_review


st.set_page_config(
    page_title="BuildPay AI | Construction Payment Review",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown(
    """
<style>
:root {
    --ink: #102033;
    --muted: #667085;
    --line: #E7ECF2;
    --surface: #FFFFFF;
    --soft: #F5F7FA;
}
.block-container { max-width: 1440px; padding-top: 2rem; }
.hero {
    padding: 1.5rem 1.7rem;
    border: 1px solid #E7ECF2;
    border-radius: 22px;
    background: linear-gradient(135deg, #ffffff 0%, #f5f8fc 100%);
    box-shadow: 0 12px 35px rgba(16, 32, 51, .06);
}
.hero h1 { margin: 0; color: #102033; font-size: 2.25rem; }
.hero p { color: #667085; margin: .45rem 0 0; font-size: 1.02rem; }
.agent-card {
    border: 1px solid #E7ECF2;
    border-radius: 16px;
    padding: 14px 16px;
    background: white;
    margin-bottom: 10px;
}
.kpi {
    border: 1px solid #E7ECF2;
    border-radius: 16px;
    padding: 16px;
    background: white;
}
.kpi .label { color: #667085; font-size: .82rem; }
.kpi .value { color: #102033; font-size: 1.25rem; font-weight: 700; margin-top: 3px; }
.human-gate {
    border: 1px solid #F2D18B;
    background: #FFF9EA;
    border-radius: 18px;
    padding: 18px;
}
.small { color: #667085; font-size: .85rem; }
</style>
""",
    unsafe_allow_html=True,
)

AGENTS = [
    ("intake", "📄", "Intake & Evidence"),
    ("contract", "📜", "Contract Compliance"),
    ("valuation", "📐", "Measurement & Valuation"),
    ("payment", "🧮", "Payment Reconciliation"),
    ("risk", "🛡️", "Risk & Exceptions"),
    ("review", "🧑‍💼", "Human Review Brief"),
]


def save_uploads(uploaded_files) -> str:
    run_dir = Path(tempfile.mkdtemp(prefix="buildpay_"))
    for uploaded in uploaded_files:
        (run_dir / uploaded.name).write_bytes(uploaded.getvalue())
    return str(run_dir)


def status_panel(container, current_name: str, state: str, progress: int):
    rows = []
    for key, icon, name in AGENTS:
        if name == current_name:
            marker = "🟢" if state == "Completed" else "🔵"
            label = f"{marker} **{name}** — {state}"
        else:
            label = f"⚪ {name}"
        rows.append(label)
    container.markdown("\n\n".join(rows))
    container.progress(min(progress, 100), text=f"{current_name}: {state}")


# ---------- Header ----------
st.markdown(
    """
<div class="hero">
  <h1>🏗️ BuildPay AI</h1>
  <p>Multi-agent construction payment review — evidence first, calculations second, human decision always.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Review setup")
    st.caption("AI assists the payment review. It never releases or authorizes money.")

    project_context = st.text_area(
        "Project context",
        placeholder=(
            "Example: Project name, contract type, payment application number, "
            "currency, reporting period, known retention %, and any special instructions."
        ),
        height=180,
    )

    uploaded_files = st.file_uploader(
        "Upload payment documents",
        type=["pdf", "docx", "xlsx", "csv", "txt", "md"],
        accept_multiple_files=True,
        help="Upload contract, payment application, certificate, schedule of values, change orders, waivers, and supporting records.",
    )

    run_button = st.button(
        "▶ Run payment review",
        type="primary",
        use_container_width=True,
        disabled=not uploaded_files,
    )

    st.divider()
    st.caption("Model")
    st.code("Groq • openai/gpt-oss-120b", language="text")
    st.caption("Orchestration: CrewAI • UI: Streamlit")


# ---------- Main workspace ----------
left, right = st.columns([1.55, 1], gap="large")

with left:
    st.subheader("Review workspace")

    if not uploaded_files:
        st.info("Upload the payment package in the sidebar to begin.")
    else:
        cols = st.columns(3)
        cols[0].markdown(
            f'<div class="kpi"><div class="label">Documents</div><div class="value">{len(uploaded_files)}</div></div>',
            unsafe_allow_html=True,
        )
        total_mb = sum(f.size for f in uploaded_files) / (1024 * 1024)
        cols[1].markdown(
            f'<div class="kpi"><div class="label">Package size</div><div class="value">{total_mb:.1f} MB</div></div>',
            unsafe_allow_html=True,
        )
        cols[2].markdown(
            '<div class="kpi"><div class="label">Decision authority</div><div class="value">Human</div></div>',
            unsafe_allow_html=True,
        )

        with st.expander("View uploaded files", expanded=False):
            for file in uploaded_files:
                st.write(f"• {file.name}")

    result_container = st.container()

with right:
    st.subheader("Agent activity")
    activity = st.empty()
    activity.markdown("⚪ Waiting for a review run.")
    progress_box = st.empty()

# ---------- Run ----------
if run_button:
    if not st.secrets.get("GROQ_API_KEY"):
        st.error("GROQ_API_KEY is missing. Add it under Streamlit → App settings → Secrets.")
        st.stop()

    run_dir = save_uploads(uploaded_files)
    results = []

    def update_status(name: str, state: str, progress: int):
        status_panel(activity, name, state, progress)

    try:
        with st.spinner("AI workforce is reviewing the payment package..."):
            results = run_payment_review(
                run_dir,
                project_context or "No additional project context was supplied.",
                update_status,
            )

        st.session_state["review_results"] = {
            item.key: {"name": item.name, "result": item.result}
            for item in results
        }
        st.session_state["run_dir"] = run_dir
        st.success("Automated review completed. Human decision gate is now active.")

    except Exception as exc:
        st.error(f"Review stopped safely: {exc}")
        st.caption(
            "No payment action was executed. Check the agent activity and deployment logs."
        )

# ---------- Results ----------
stored = st.session_state.get("review_results", {})
if stored:
    st.divider()
    st.subheader("Agent reports")

    tabs = st.tabs(
        [
            "📄 Intake",
            "📜 Contract",
            "📐 Valuation",
            "🧮 Payment",
            "🛡️ Risk",
            "🧑‍💼 Human Brief",
        ]
    )

    keys = ["intake", "contract", "valuation", "payment", "risk", "review"]
    for tab, key in zip(tabs, keys):
        with tab:
            report = stored.get(key)
            if report:
                st.markdown(report["result"])
            else:
                st.info("No report was produced for this stage.")

    st.divider()
    st.markdown(
        """
<div class="human-gate">
<h3>🧑‍⚖️ Human decision gate</h3>
<p>These controls are deliberately outside the agent workflow. Selecting an option below records a human workflow decision only; it does not send a payment, modify an ERP, or authorize a bank transfer.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    decision = st.radio(
        "Human reviewer decision",
        [
            "Pending human decision",
            "Approve for next internal process",
            "Reject / return for correction",
            "Request additional evidence",
        ],
        horizontal=True,
    )

    reviewer_note = st.text_area(
        "Reviewer note",
        placeholder="Explain the human decision or the evidence still required.",
        height=100,
    )

    if st.button("Record human decision", type="primary"):
        st.session_state["human_decision"] = {
            "decision": decision,
            "note": reviewer_note,
        }
        st.success("Human decision recorded in the current Streamlit session.")

    if st.session_state.get("human_decision"):
        st.json(st.session_state["human_decision"])

    st.download_button(
        "Download review bundle (JSON)",
        data=json.dumps(
            {
                "agents": stored,
                "human_decision": st.session_state.get("human_decision"),
            },
            indent=2,
        ),
        file_name="buildpay_review_bundle.json",
        mime="application/json",
        use_container_width=True,
    )

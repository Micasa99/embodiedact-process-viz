"""
EmbodiedAct: Process-Level Visualization for ICML 2026
======================================================

Interactive dashboard showing how EmbodiedAct allocates compute across
its four cognitive modules (M_plan, M_code, M_perc, M_ref) during
scientific problem solving.

All traces are illustrative simulations consistent with the measured
token distribution in Table 12 of the paper.
"""
import json
from pathlib import Path

import plotly.io as pio
import streamlit as st

# ── Page config ──
st.set_page_config(
    page_title="EmbodiedAct Process Visualization",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

FIGURES_DIR = Path(__file__).parent / "figures"

# ── Load figures ──
@st.cache_data
def load_figure(name: str):
    path = FIGURES_DIR / f"{name}.json"
    if not path.exists():
        return None
    return pio.from_json(path.read_text(encoding="utf-8"))

@st.cache_data
def load_summary():
    path = FIGURES_DIR / "bundles_summary.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []

FIGURE_META = [
    ("p1_causal_timeline",
     "P1. Process-Level Causal Timeline",
     "Swimlane timeline of a PID controller design task. Shows how M_perc detects "
     "overshoot during simulation and triggers a Hot-Fix before the simulation terminates. "
     "The bottom panel shows the physical step response before and after intervention.",
     "eB6g"),
    ("p2_token_asymmetry",
     "P2. Token Pulse Asymmetry",
     "Mirrored area chart showing input tokens (upward) vs output tokens (downward) "
     "over time. The 93% input / 7% output split demonstrates that EmbodiedAct's "
     "overhead comes from runtime state observation, not verbose output-side reasoning.",
     "9nVe"),
    ("p3_time_occupancy",
     "P3. Time Occupancy by Task Difficulty",
     "Wall-clock time breakdown stratified by task difficulty. Easy tasks (1-iteration) "
     "show minimal perception overhead, while hard tasks invest heavily in simulation "
     "and perception — demonstrating adaptive compute allocation.",
     "4dqt"),
    ("p4_butterfly_comparison",
     "P4. Success vs Failure Token Structure",
     "Butterfly comparison of normalized token profiles. Successful runs invest in "
     "planning and perception early, while failed runs show late-stage M_code and "
     "M_ref inflation. The difference plot highlights the structural gap.",
     "eB6g"),
    ("p5_module_roi",
     "P5. Module Return on Token Investment",
     "M_perc (18% of tokens) occupies the highest-ROI region: each 1% of token "
     "investment yields 0.78pp accuracy improvement, 1.66x higher than M_ref. "
     "Runtime perception is not overhead — it is the most valuable computation.",
     "9nVe"),
    ("p6_token_waterfall",
     "P6. Per-Iteration Token Waterfall",
     "Token accumulation across a 4-iteration optimization task. M_code decreases "
     "in subsequent iterations (targeted repair, not regeneration) while M_perc "
     "remains stable — the system learns to fix rather than rewrite.",
     "9nVe"),
    ("p7_multi_case_gallery",
     "P7. Multi-Case Process Gallery",
     "Small-multiples view of all 14 simulated cases. Easy 1-iteration tasks are "
     "compact; hard multi-iteration tasks show expanded timelines with warning events "
     "and repair cycles. The system adapts its compute budget per task.",
     "4dqt"),
    ("p8_domain_radar",
     "P8. Cross-Domain Module Allocation",
     "Radar chart showing how module allocation varies by engineering domain. "
     "Control Systems emphasize perception; Signal/Digital emphasize code generation; "
     "the framework adapts its cognitive resource distribution per domain type.",
     "4dqt"),
]

# ── Sidebar ──
st.sidebar.title("EmbodiedAct")
st.sidebar.caption("Process-Level Visualization")
st.sidebar.markdown("---")

st.sidebar.markdown("**Paper:** Grounding LLMs in Scientific Discovery via Embodied Actions")
st.sidebar.markdown("**Venue:** ICML 2026 (Under Review)")
st.sidebar.markdown("---")

view_mode = st.sidebar.radio(
    "View Mode",
    ["All Figures", "Single Figure", "Reviewer-Focused"],
    index=0,
)

selected_figure = None
selected_reviewer = None

if view_mode == "Single Figure":
    options = {meta[1]: meta[0] for meta in FIGURE_META}
    choice = st.sidebar.selectbox("Select Figure", list(options.keys()))
    selected_figure = options[choice]

if view_mode == "Reviewer-Focused":
    selected_reviewer = st.sidebar.selectbox(
        "Select Reviewer",
        ["9nVe — Token Efficiency", "4dqt — Adaptive Compute", "eB6g — Process Evidence"],
    ).split(" — ")[0]

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Data Note:** All traces are illustrative simulations "
    "consistent with the measured token distribution in Table 12."
)

# Summary stats
summary = load_summary()
if summary:
    n_success = sum(1 for s in summary if s["is_success"])
    n_failure = len(summary) - n_success
    total_tok = sum(s["total_tokens"] for s in summary)
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Trace Statistics**")
    col1, col2 = st.sidebar.columns(2)
    col1.metric("Cases", len(summary))
    col2.metric("Domains", len(set(s["domain"].split("(")[0].strip() for s in summary)))
    col1.metric("Success", n_success)
    col2.metric("Failure", n_failure)

# ── Main content ──
st.title("EmbodiedAct: Process-Level Visualization")
st.markdown(
    "Interactive figures showing how EmbodiedAct's four cognitive modules "
    "(**M_plan**, **M_code**, **M_perc**, **M_ref**) coordinate during "
    "scientific problem solving. Hover for details, zoom to explore."
)

# Key claims banner
with st.expander("Key Claims Supported by These Visualizations", expanded=False):
    st.markdown("""
    | Claim | Evidence | Figures |
    |-------|----------|---------|
    | Extra overhead is input-side observation, not output-side CoT | 93% input / 7% output token split | P2, P5 |
    | M_perc is the highest-ROI module | 0.78pp/% vs 0.47pp/% for M_ref | P5 |
    | System is adaptive, not fixed overhead | Easy tasks: minimal perception; Hard tasks: heavy perception | P3, P7 |
    | Token structure matters more than total | Success: early M_plan+M_perc; Failure: late M_code inflation | P4 |
    | Runtime perception enables mid-execution intervention | Warning → Interrupt → HotFix → Recovery | P1 |
    | Subsequent iterations get cheaper (targeted repair) | M_code decreases: 15.4K → 8.2K → 5.1K per iteration | P6 |
    | Module allocation adapts per domain | Control: heavy M_perc; Digital: heavy M_code | P8 |
    """)


def render_figure(fig_id, title, description, reviewer):
    """Render a single figure with its description."""
    reviewer_badge = {
        "9nVe": "🔵 Reviewer 9nVe — Token Efficiency",
        "4dqt": "🟠 Reviewer 4dqt — Adaptive Compute",
        "eB6g": "🟢 Reviewer eB6g — Process Evidence",
    }

    st.markdown(f"### {title}")
    st.caption(f"Addresses: {reviewer_badge.get(reviewer, reviewer)}")

    fig = load_figure(fig_id)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True, theme=None)
    else:
        st.warning(f"Figure data not found: {fig_id}")

    with st.expander("Figure Description"):
        st.markdown(description)


if view_mode == "All Figures":
    for fig_id, title, desc, reviewer in FIGURE_META:
        render_figure(fig_id, title, desc, reviewer)
        st.markdown("---")

elif view_mode == "Single Figure":
    for fig_id, title, desc, reviewer in FIGURE_META:
        if fig_id == selected_figure:
            render_figure(fig_id, title, desc, reviewer)
            break

elif view_mode == "Reviewer-Focused":
    st.info(f"Showing figures relevant to Reviewer **{selected_reviewer}**")
    found = False
    for fig_id, title, desc, reviewer in FIGURE_META:
        if reviewer == selected_reviewer:
            render_figure(fig_id, title, desc, reviewer)
            st.markdown("---")
            found = True
    if not found:
        st.warning("No figures found for this reviewer.")

# Footer
st.markdown("---")
st.caption(
    "EmbodiedAct: Grounding LLMs in Scientific Discovery via Embodied Actions | "
    "ICML 2026 Submission | "
    "Illustrative simulated traces consistent with Table 12"
)

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
import streamlit.components.v1 as components

# ── Page config ──
st.set_page_config(
    page_title="EmbodiedAct Process Visualization",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

FIGURES_DIR = Path(__file__).parent / "figures"
TRACE_PATH = FIGURES_DIR / "trace_bundle_hero.json"


# ── Load helpers ──
@st.cache_data
def load_figure(name: str):
    path = FIGURES_DIR / f"{name}.json"
    if not path.exists():
        return None
    fig = pio.from_json(path.read_text(encoding="utf-8"))
    fig.update_layout(template="plotly_white")
    return fig


@st.cache_data
def load_summary():
    path = FIGURES_DIR / "bundles_summary.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


@st.cache_data
def load_hero_bundle():
    path = FIGURES_DIR / "trace_bundle_hero.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


@st.cache_data
def render_p1_html():
    """Render the custom SVG timeline for P1."""
    bundle = load_hero_bundle()
    if bundle is None:
        return None
    from timeline_renderer import render_timeline_html
    return render_timeline_html(bundle, width=1100, show_signal=True)


FIGURE_META = [
    ("p1_causal_timeline",
     "P1. Process-Level Causal Timeline",
     "Swimlane timeline of a PID controller design task. Shows how **M_perc** detects "
     "overshoot during simulation and triggers a **Hot-Fix** before the simulation terminates. "
     "The bottom panel shows the physical step response before and after intervention.\n\n"
     "*Hover over any span bar for detailed token/timing information.*",
     "eB6g"),
    ("p2_token_asymmetry",
     "P2. Token Pulse Asymmetry",
     "Mirrored area chart showing input tokens (upward) vs output tokens (downward) "
     "over time. The **93% input / 7% output** split demonstrates that EmbodiedAct's "
     "overhead comes from runtime state observation, not verbose output-side reasoning.",
     "9nVe"),
    ("p3_time_occupancy",
     "P3. Time Occupancy by Task Difficulty",
     "Wall-clock time breakdown stratified by task difficulty. Easy tasks (1-iteration) "
     "show minimal perception overhead, while hard tasks invest heavily in simulation "
     "and perception — demonstrating **adaptive compute allocation**.",
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
     "investment yields **0.78pp** accuracy improvement, **1.66x** higher than M_ref. "
     "Runtime perception is not overhead — it is the most valuable computation.",
     "9nVe"),
    ("p6_token_waterfall",
     "P6. Per-Iteration Token Waterfall",
     "Token accumulation across a 4-iteration optimization task. M_code **decreases** "
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
with st.sidebar:
    st.markdown(
        '<div style="text-align:center; padding: 8px 0 12px;">'
        '<span style="font-size:28px;">🔬</span><br>'
        '<span style="font-size:18px; font-weight:700; color:#1E293B;">EmbodiedAct</span><br>'
        '<span style="font-size:11px; color:#64748B; letter-spacing:1px;">PROCESS VISUALIZATION</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    st.markdown(
        '<div style="background:#F8FAFC; border-radius:8px; padding:10px 12px; border:1px solid #E2E8F0;">'
        '<div style="font-size:11px; color:#64748B; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Paper</div>'
        '<div style="font-size:12px; color:#1E293B; font-weight:500;">Grounding LLMs in Scientific Discovery via Embodied Actions</div>'
        '<div style="font-size:11px; color:#94A3B8; margin-top:4px;">ICML 2026 · Under Review</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("")

    view_mode = st.radio(
        "**View Mode**",
        ["All Figures", "Single Figure", "Reviewer-Focused"],
        index=0,
    )

    selected_figure = None
    selected_reviewer = None

    if view_mode == "Single Figure":
        options = {meta[1]: meta[0] for meta in FIGURE_META}
        choice = st.selectbox("Select Figure", list(options.keys()))
        selected_figure = options[choice]

    if view_mode == "Reviewer-Focused":
        selected_reviewer = st.selectbox(
            "Select Reviewer",
            ["9nVe — Token Efficiency", "4dqt — Adaptive Compute", "eB6g — Process Evidence"],
        ).split(" — ")[0]

    st.markdown("---")

    # Summary stats with visual hierarchy
    summary = load_summary()
    if summary:
        n_success = sum(1 for s in summary if s["is_success"])
        n_failure = len(summary) - n_success
        n_domains = len(set(s["domain"].split("(")[0].strip() for s in summary))
        total_tok = sum(s["total_tokens"] for s in summary)

        st.markdown(
            '<div style="font-size:11px; color:#64748B; text-transform:uppercase; '
            'letter-spacing:0.5px; margin-bottom:8px;">Trace Statistics</div>',
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        c1.metric("Cases", len(summary))
        c2.metric("Domains", n_domains)
        c1.metric("Success", n_success, delta=f"{100*n_success/len(summary):.0f}%")
        c2.metric("Failure", n_failure)

        st.markdown(
            f'<div style="font-size:10px; color:#94A3B8; margin-top:4px;">'
            f'Total tokens: {total_tok:,}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.caption(
        "All traces are illustrative simulations "
        "consistent with the measured token distribution in Table 12."
    )

# ── Main content ──
st.markdown(
    '<h1 style="margin-bottom:4px;">EmbodiedAct: Process-Level Visualization</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    "Interactive figures showing how EmbodiedAct's four cognitive modules "
    "(**M_plan**, **M_code**, **M_perc**, **M_ref**) coordinate during "
    "scientific problem solving."
)

# Key claims banner
with st.expander("**Key Claims Supported by These Visualizations**", expanded=False):
    st.markdown("""
| Claim | Evidence | Figures |
|-------|----------|---------|
| Extra overhead is input-side observation, not output-side CoT | 93% input / 7% output token split | P2, P5 |
| M_perc is the highest-ROI module | 0.78pp/% vs 0.47pp/% for M_ref | P5 |
| System is adaptive, not fixed overhead | Easy tasks: minimal perception; Hard tasks: heavy perception | P3, P7 |
| Token structure matters more than total | Success: early M_plan+M_perc; Failure: late M_code inflation | P4 |
| Runtime perception enables mid-execution intervention | Warning → Interrupt → HotFix → Recovery | P1 |
| Subsequent iterations get cheaper (targeted repair) | M_code decreases per iteration | P6 |
| Module allocation adapts per domain | Control: heavy M_perc; Digital: heavy M_code | P8 |
""")


def render_figure(fig_id, title, description, reviewer):
    """Render a single figure with its description."""
    badge_styles = {
        "9nVe": ("🔵", "#DBEAFE", "#1E40AF"),
        "4dqt": ("🟠", "#FEF3C7", "#92400E"),
        "eB6g": ("🟢", "#D1FAE5", "#065F46"),
    }
    badge_names = {
        "9nVe": "Reviewer 9nVe — Token Efficiency",
        "4dqt": "Reviewer 4dqt — Adaptive Compute",
        "eB6g": "Reviewer eB6g — Process Evidence",
    }

    icon, bg, fg = badge_styles.get(reviewer, ("⚪", "#F3F4F6", "#374151"))
    badge_name = badge_names.get(reviewer, reviewer)

    st.markdown(f"### {title}")
    st.markdown(
        f'<span style="background:{bg}; color:{fg}; padding:3px 10px; border-radius:12px; '
        f'font-size:11px; font-weight:500;">{icon} {badge_name}</span>',
        unsafe_allow_html=True,
    )

    # P1 uses custom SVG renderer
    if fig_id == "p1_causal_timeline":
        p1_html = render_p1_html()
        if p1_html:
            components.html(p1_html, height=620, scrolling=False)
        else:
            # Fallback to Plotly
            fig = load_figure(fig_id)
            if fig:
                st.plotly_chart(fig, use_container_width=True, theme=None)
            else:
                st.warning("P1 data not available.")
    else:
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
    for fig_id, title, desc, reviewer in FIGURE_META:
        if reviewer == selected_reviewer:
            render_figure(fig_id, title, desc, reviewer)
            st.markdown("---")

# Footer
st.markdown("---")
st.caption(
    "EmbodiedAct: Grounding LLMs in Scientific Discovery via Embodied Actions · "
    "ICML 2026 Submission · "
    "Illustrative simulated traces consistent with Table 12"
)

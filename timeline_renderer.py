"""
Custom SVG Timeline Renderer for EmbodiedAct P1 Figure.

Generates a high-quality HTML/SVG/JS timeline with:
- Clean swimlane layout with labeled rows
- Color-coded span bars with rounded corners and token badges
- Smooth bezier curve arrows for causal chains (Warning → Interrupt → HotFix)
- Strong iteration band separators with phase labels
- Rich hover tooltips with detailed info
- Aligned physical signal panel below
- Professional typography and color system
"""
from __future__ import annotations

import html
import json
import math
from typing import Any, Dict, List, Optional, Sequence

# ── Color System ──
# Carefully tuned for visual hierarchy and accessibility
COLORS = {
    "M_plan":  {"fill": "#3B82F6", "light": "#DBEAFE", "text": "#1E40AF", "label": "Strategic Planner"},
    "M_code":  {"fill": "#EF4444", "light": "#FEE2E2", "text": "#991B1B", "label": "Primitive Generator"},
    "TRACKER": {"fill": "#6B7280", "light": "#F3F4F6", "text": "#374151", "label": "Operation Tracker"},
    "ENV":     {"fill": "#F59E0B", "light": "#FEF3C7", "text": "#92400E", "label": "Simulation Env."},
    "M_perc":  {"fill": "#10B981", "light": "#D1FAE5", "text": "#065F46", "label": "Perception Engine"},
    "M_ref":   {"fill": "#8B5CF6", "light": "#EDE9FE", "text": "#5B21B6", "label": "Reflective Maker"},
}

SWIMLANE_ORDER = ["M_plan", "M_code", "TRACKER", "ENV", "M_perc", "M_ref"]
PROFILE_MODULES = ["M_plan", "M_code", "M_perc", "M_ref"]

# ── Layout Constants ──
LANE_H = 52
LANE_GAP = 6
LABEL_W = 175
MARGIN_T = 65
MARGIN_B = 20
MARGIN_R = 30
BAR_H = 34
BAR_R = 5  # border radius
SIGNAL_H = 160
AXIS_H = 32
TOOLTIP_W = 280


def _sf(v, d=0.0):
    try:
        return float(v) if v is not None else d
    except Exception:
        return d


def _si(v, d=0):
    try:
        return int(round(float(v))) if v is not None else d
    except Exception:
        return d


def _esc(s: str) -> str:
    return html.escape(str(s))


def render_timeline_html(
    bundle: Dict[str, Any],
    width: int = 1100,
    show_signal: bool = True,
) -> str:
    """Render a complete interactive SVG timeline from a trace bundle."""

    wall_ms = max(1.0, _sf(bundle.get("wall_clock_ms")))
    wall_s = wall_ms / 1000.0
    spans = bundle.get("spans", [])
    events = bundle.get("events", [])

    chart_w = width - LABEL_W - MARGIN_R
    n_lanes = len(SWIMLANE_ORDER)
    lanes_h = n_lanes * (LANE_H + LANE_GAP) - LANE_GAP
    total_h = MARGIN_T + lanes_h + AXIS_H + (SIGNAL_H + 30 if show_signal else 0) + MARGIN_B

    def t2x(ms):
        return LABEL_W + (ms / wall_ms) * chart_w

    def lane_y(mod):
        idx = SWIMLANE_ORDER.index(mod) if mod in SWIMLANE_ORDER else 0
        return MARGIN_T + idx * (LANE_H + LANE_GAP)

    def lane_cy(mod):
        return lane_y(mod) + LANE_H / 2

    # ── Compute iteration boundaries ──
    iter_bounds = {}
    for sp in spans:
        it = sp.get("iteration_id", 1)
        s_ms = _sf(sp.get("start_ms"))
        e_ms = _sf(sp.get("end_ms"))
        if it not in iter_bounds:
            iter_bounds[it] = [s_ms, e_ms]
        else:
            iter_bounds[it][0] = min(iter_bounds[it][0], s_ms)
            iter_bounds[it][1] = max(iter_bounds[it][1], e_ms)

    # ── Build SVG parts ──
    svg_parts = []

    # Background
    svg_parts.append(f'<rect width="{width}" height="{total_h}" fill="#FAFBFC" rx="8"/>')

    # Iteration bands
    band_fills = ["#EFF6FF", "#FFFBEB", "#ECFDF5", "#FDF2F8", "#F5F3FF"]
    for it in sorted(iter_bounds):
        x0 = t2x(iter_bounds[it][0])
        x1 = t2x(iter_bounds[it][1])
        fill = band_fills[(it - 1) % len(band_fills)]
        svg_parts.append(
            f'<rect x="{x0}" y="{MARGIN_T - 5}" width="{x1-x0}" height="{lanes_h + 10}" '
            f'fill="{fill}" rx="4" opacity="0.7"/>'
        )
        # Iteration label at top
        mx = (x0 + x1) / 2
        svg_parts.append(
            f'<text x="{mx}" y="{MARGIN_T - 12}" text-anchor="middle" '
            f'font-size="11" font-weight="600" fill="#64748B" font-family="system-ui, sans-serif">'
            f'Iteration {it}</text>'
        )
        # Separator line between iterations
        if it > 1:
            svg_parts.append(
                f'<line x1="{x0}" y1="{MARGIN_T - 5}" x2="{x0}" y2="{MARGIN_T + lanes_h + 5}" '
                f'stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="6,4"/>'
            )

    # Swimlane labels and backgrounds
    for mod in SWIMLANE_ORDER:
        y = lane_y(mod)
        info = COLORS[mod]
        # Lane background stripe
        svg_parts.append(
            f'<rect x="{LABEL_W - 2}" y="{y}" width="{chart_w + 4}" height="{LANE_H}" '
            f'fill="{info["light"]}" opacity="0.25" rx="3"/>'
        )
        # Module color indicator bar
        svg_parts.append(
            f'<rect x="{4}" y="{y + 8}" width="4" height="{LANE_H - 16}" '
            f'fill="{info["fill"]}" rx="2"/>'
        )
        # Label
        svg_parts.append(
            f'<text x="14" y="{y + LANE_H/2 - 6}" font-size="11" font-weight="600" '
            f'fill="{info["text"]}" font-family="system-ui, sans-serif" dominant-baseline="middle">'
            f'{_esc(info["label"])}</text>'
        )
        # Formal notation
        formal = mod.replace("_", "<tspan font-style=\"italic\" font-size=\"9\">") + "</tspan>" if "_" in mod else mod
        svg_parts.append(
            f'<text x="14" y="{y + LANE_H/2 + 10}" font-size="9" fill="#94A3B8" '
            f'font-family="system-ui, sans-serif">{_esc(mod)}</text>'
        )

    # ── Span bars ──
    span_rects = []  # Store for arrow computation
    for sp in spans:
        mod = sp.get("module")
        if mod not in SWIMLANE_ORDER:
            continue
        s_ms = _sf(sp.get("start_ms"))
        e_ms = _sf(sp.get("end_ms"))
        x = t2x(s_ms)
        w = max(3, t2x(e_ms) - x)
        y = lane_y(mod) + (LANE_H - BAR_H) / 2
        info = COLORS[mod]
        status = sp.get("status", "ok")
        opacity = "0.92" if status == "ok" else "0.55"
        stroke = info["fill"] if status == "ok" else "#F59E0B" if status == "warning" else "#EF4444"
        stroke_w = "1" if status == "ok" else "2"

        inp = _si(sp.get("input_tokens"))
        out = _si(sp.get("output_tokens"))
        dur_ms = _sf(sp.get("duration_ms"))
        name = sp.get("name", "").replace("_", " ")
        zt = sp.get("zt", "")

        # Hover data
        hover_data = json.dumps({
            "module": mod, "name": name, "status": status,
            "input_tokens": inp, "output_tokens": out,
            "duration_ms": round(dur_ms, 1), "zt": zt,
            "notes": sp.get("notes", ""),
        })

        span_rects.append({
            "mod": mod, "x": x, "w": w, "y": y, "cx": x + w / 2, "cy": y + BAR_H / 2,
            "status": status, "span_type": sp.get("span_type"),
            "start_ms": s_ms, "end_ms": e_ms, "name": name,
            "iteration_id": sp.get("iteration_id", 1),
        })

        # Bar
        svg_parts.append(
            f'<rect class="span-bar" x="{x}" y="{y}" width="{w}" height="{BAR_H}" '
            f'rx="{BAR_R}" fill="{info["fill"]}" opacity="{opacity}" '
            f'stroke="{stroke}" stroke-width="{stroke_w}" '
            f'data-hover=\'{_esc(hover_data)}\' '
            f'style="cursor:pointer; transition: opacity 0.15s;"/>'
        )

        # Token badge (only if bar wide enough)
        if w > 55:
            badge_text = f"I:{inp}" if inp > 0 else ""
            if out > 0:
                badge_text += f" O:{out}" if badge_text else f"O:{out}"
            if badge_text:
                svg_parts.append(
                    f'<text x="{x + w/2}" y="{y + BAR_H/2 + 1}" text-anchor="middle" '
                    f'font-size="8.5" fill="white" font-family="monospace" '
                    f'dominant-baseline="middle" pointer-events="none" opacity="0.9">'
                    f'{_esc(badge_text)}</text>'
                )
        # Duration badge below bar
        if w > 40 and dur_ms > 100:
            svg_parts.append(
                f'<text x="{x + w/2}" y="{y + BAR_H + 10}" text-anchor="middle" '
                f'font-size="7.5" fill="{info["text"]}" font-family="system-ui, sans-serif" '
                f'opacity="0.6" pointer-events="none">{dur_ms:.0f}ms</text>'
            )

    # ── Event markers ──
    for evt in events:
        mod = evt.get("module")
        if mod not in SWIMLANE_ORDER:
            continue
        t_ms = _sf(evt.get("timestamp_ms"))
        etype = evt.get("event_type", "")
        severity = evt.get("severity", "info")
        cx = t2x(t_ms)
        cy = lane_cy(mod)

        if etype == "interrupt":
            # X marker
            s = 7
            svg_parts.append(
                f'<g transform="translate({cx},{cy})">'
                f'<line x1="-{s}" y1="-{s}" x2="{s}" y2="{s}" stroke="#DC2626" stroke-width="2.5" stroke-linecap="round"/>'
                f'<line x1="{s}" y1="-{s}" x2="-{s}" y2="{s}" stroke="#DC2626" stroke-width="2.5" stroke-linecap="round"/>'
                f'</g>'
            )
            svg_parts.append(
                f'<text x="{cx}" y="{cy - 14}" text-anchor="middle" '
                f'font-size="8" fill="#DC2626" font-weight="600" font-family="system-ui">INTERRUPT</text>'
            )
        elif severity == "warning" and etype not in ("operation_progress",):
            # Diamond marker
            s = 5
            svg_parts.append(
                f'<polygon points="{cx},{cy-s} {cx+s},{cy} {cx},{cy+s} {cx-s},{cy}" '
                f'fill="#F59E0B" stroke="#D97706" stroke-width="1"/>'
            )
            hook = evt.get("hook_name", "")
            if hook:
                short = hook.split(":")[-1][:18]
                svg_parts.append(
                    f'<text x="{cx}" y="{cy - 10}" text-anchor="middle" '
                    f'font-size="7.5" fill="#D97706" font-family="system-ui" font-style="italic">'
                    f'{_esc(short)}</text>'
                )
        elif severity == "error":
            # Square marker
            s = 5
            svg_parts.append(
                f'<rect x="{cx-s}" y="{cy-s}" width="{2*s}" height="{2*s}" '
                f'fill="#DC2626" stroke="#991B1B" stroke-width="1" rx="1"/>'
            )

    # ── Causal arrows (Warning → Interrupt → HotFix) ──
    # Find warning events and pair with subsequent repair spans
    interrupts = [e for e in events if e.get("event_type") == "interrupt"]
    repairs = [sr for sr in span_rects if sr.get("span_type") == "repair"]

    for intr in interrupts[:3]:  # Max 3 arrows
        t_intr = _sf(intr.get("timestamp_ms"))
        mod_intr = intr.get("module")
        if mod_intr not in SWIMLANE_ORDER:
            continue

        # Find the next repair span after this interrupt
        best_repair = None
        for rep in repairs:
            if rep["start_ms"] > t_intr - 100:
                best_repair = rep
                break

        if best_repair is None:
            continue

        # Arrow from interrupt point to repair bar start
        x1 = t2x(t_intr)
        y1 = lane_cy(mod_intr)
        x2 = best_repair["x"]
        y2 = best_repair["cy"]

        # Compute bezier control points for a smooth curve
        dx = x2 - x1
        dy = y2 - y1
        # Control points create a nice arc
        cx1 = x1 + dx * 0.3
        cy1 = y1 - abs(dy) * 0.4 - 20
        cx2 = x2 - dx * 0.3
        cy2 = y2 - abs(dy) * 0.4 - 20

        # Arrow path
        svg_parts.append(
            f'<path d="M{x1},{y1} C{cx1},{cy1} {cx2},{cy2} {x2},{y2}" '
            f'fill="none" stroke="#DC2626" stroke-width="1.8" '
            f'stroke-dasharray="5,3" opacity="0.7" '
            f'marker-end="url(#arrowhead)"/>'
        )

        # Label on the arrow
        label_x = (x1 + x2) / 2
        label_y = min(cy1, cy2) - 4
        svg_parts.append(
            f'<text x="{label_x}" y="{label_y}" text-anchor="middle" '
            f'font-size="8" fill="#DC2626" font-weight="500" font-family="system-ui">'
            f'Hot-Fix Loop</text>'
        )

    # ── Time axis ──
    axis_y = MARGIN_T + lanes_h + 8
    svg_parts.append(
        f'<line x1="{LABEL_W}" y1="{axis_y}" x2="{LABEL_W + chart_w}" y2="{axis_y}" '
        f'stroke="#CBD5E1" stroke-width="1"/>'
    )

    # Tick marks
    n_ticks = min(12, max(4, int(wall_s / 1.5)))
    for i in range(n_ticks + 1):
        t_s = wall_s * i / n_ticks
        x = t2x(t_s * 1000)
        svg_parts.append(
            f'<line x1="{x}" y1="{axis_y}" x2="{x}" y2="{axis_y + 5}" stroke="#94A3B8" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{x}" y="{axis_y + 18}" text-anchor="middle" font-size="9" '
            f'fill="#64748B" font-family="system-ui">{t_s:.1f}s</text>'
        )

    svg_parts.append(
        f'<text x="{LABEL_W + chart_w / 2}" y="{axis_y + 30}" text-anchor="middle" '
        f'font-size="10" fill="#475569" font-family="system-ui">Wall-clock Time</text>'
    )

    # ── Signal panel (aligned x-axis) ──
    signal_svg = ""
    sig = bundle.get("signal_data", {})
    if show_signal and sig and "t" in sig and "y_before" in sig:
        sig_y_top = axis_y + AXIS_H + 10
        sig_plot_h = SIGNAL_H - 40

        t_arr = sig["t"]
        y_arr = sig["y_before"]
        y_min = min(y_arr) - 0.1
        y_max = max(y_arr) + 0.15
        y_range = max(0.01, y_max - y_min)

        # Signal panel background
        signal_svg += (
            f'<rect x="{LABEL_W - 2}" y="{sig_y_top}" width="{chart_w + 4}" height="{SIGNAL_H - 10}" '
            f'fill="white" stroke="#E2E8F0" stroke-width="1" rx="4"/>'
        )

        # Signal panel label
        ylabel = sig.get("ylabel", "Signal")
        signal_svg += (
            f'<text x="{LABEL_W - 10}" y="{sig_y_top + sig_plot_h / 2}" '
            f'text-anchor="middle" font-size="9" fill="#64748B" font-family="system-ui" '
            f'transform="rotate(-90,{LABEL_W - 10},{sig_y_top + sig_plot_h / 2})">'
            f'{_esc(ylabel)}</text>'
        )

        def sig_x(t_val):
            # Map signal time to same x-axis as timeline
            frac = t_val / max(t_arr) if max(t_arr) > 0 else 0
            return LABEL_W + frac * chart_w

        def sig_y(y_val):
            frac = (y_val - y_min) / y_range
            return sig_y_top + sig_plot_h - frac * sig_plot_h + 10

        # Target line
        if "target" in sig:
            ty = sig_y(sig["target"])
            signal_svg += (
                f'<line x1="{LABEL_W}" y1="{ty}" x2="{LABEL_W + chart_w}" y2="{ty}" '
                f'stroke="#94A3B8" stroke-width="1" stroke-dasharray="4,3" opacity="0.6"/>'
            )
            signal_svg += (
                f'<text x="{LABEL_W + chart_w + 3}" y="{ty + 3}" font-size="8" '
                f'fill="#94A3B8" font-family="system-ui">target</text>'
            )

        # Before hot-fix signal
        points = " ".join(f"{sig_x(t)},{sig_y(y)}" for t, y in zip(t_arr, y_arr))
        signal_svg += (
            f'<polyline points="{points}" fill="none" stroke="#EF4444" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        )

        # After hot-fix signal
        if "y_after" in sig:
            y2_arr = sig["y_after"]
            points2 = " ".join(f"{sig_x(t)},{sig_y(y)}" for t, y in zip(t_arr, y2_arr))
            signal_svg += (
                f'<polyline points="{points2}" fill="none" stroke="#10B981" '
                f'stroke-width="2" stroke-dasharray="6,3" stroke-linecap="round"/>'
            )

        # Warning detection marker
        if "warning_time" in sig:
            wt = sig["warning_time"]
            wx = sig_x(wt)
            signal_svg += (
                f'<line x1="{wx}" y1="{sig_y_top + 5}" x2="{wx}" y2="{sig_y_top + sig_plot_h + 15}" '
                f'stroke="#F59E0B" stroke-width="1.5" stroke-dasharray="4,2"/>'
            )
            # Find the y value at warning time
            w_idx = min(range(len(t_arr)), key=lambda i: abs(t_arr[i] - wt))
            wy = sig_y(y_arr[w_idx])
            signal_svg += (
                f'<circle cx="{wx}" cy="{wy}" r="5" fill="#F59E0B" stroke="white" stroke-width="2"/>'
            )
            signal_svg += (
                f'<text x="{wx + 8}" y="{wy - 8}" font-size="9" fill="#D97706" '
                f'font-weight="600" font-family="system-ui">Warning detected</text>'
            )

        # Legend
        leg_x = LABEL_W + 10
        leg_y = sig_y_top + sig_plot_h + 22
        signal_svg += (
            f'<line x1="{leg_x}" y1="{leg_y}" x2="{leg_x+20}" y2="{leg_y}" '
            f'stroke="#EF4444" stroke-width="2"/>'
            f'<text x="{leg_x+25}" y="{leg_y+3}" font-size="9" fill="#64748B" '
            f'font-family="system-ui">{_esc(sig.get("label_before", "Before Hot-Fix"))}</text>'
        )
        if "y_after" in sig:
            leg_x2 = leg_x + 160
            signal_svg += (
                f'<line x1="{leg_x2}" y1="{leg_y}" x2="{leg_x2+20}" y2="{leg_y}" '
                f'stroke="#10B981" stroke-width="2" stroke-dasharray="6,3"/>'
                f'<text x="{leg_x2+25}" y="{leg_y+3}" font-size="9" fill="#64748B" '
                f'font-family="system-ui">{_esc(sig.get("label_after", "After Hot-Fix"))}</text>'
            )

    # ── Title ──
    domain = bundle.get("domain", "")
    prob = bundle.get("problem_id", "")
    success = "Success" if bundle.get("is_success") else "Failure"
    iters = bundle.get("iterations", 1)
    total_tok = _si(bundle.get("token_totals", {}).get("total_tokens"))

    title_svg = (
        f'<text x="{width / 2}" y="22" text-anchor="middle" font-size="14" '
        f'font-weight="700" fill="#1E293B" font-family="system-ui">'
        f'Process-Level Causal Timeline: {_esc(domain)}</text>'
        f'<text x="{width / 2}" y="40" text-anchor="middle" font-size="10" '
        f'fill="#64748B" font-family="system-ui">'
        f'{_esc(prob)} · {success} · {iters} iterations · {total_tok:,} tokens</text>'
    )

    # ── Assemble SVG ──
    arrowhead_def = (
        '<defs>'
        '<marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">'
        '<polygon points="0 0, 8 3, 0 6" fill="#DC2626" opacity="0.7"/>'
        '</marker>'
        '</defs>'
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h}" '
        f'viewBox="0 0 {width} {total_h}" '
        f'style="font-family: system-ui, -apple-system, sans-serif;">'
        f'{arrowhead_def}'
        f'{title_svg}'
        + "\n".join(svg_parts)
        + signal_svg
        + '</svg>'
    )

    # ── Wrap in HTML with tooltip JS ──
    full_html = f"""<!DOCTYPE html>
<html>
<head>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #FAFBFC; }}
  .container {{ position: relative; display: inline-block; }}
  .span-bar:hover {{ opacity: 1 !important; filter: brightness(1.1); }}
  #tooltip {{
    position: absolute;
    display: none;
    background: rgba(15, 23, 42, 0.95);
    color: #F1F5F9;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 12px;
    font-family: system-ui, sans-serif;
    line-height: 1.6;
    max-width: {TOOLTIP_W}px;
    pointer-events: none;
    z-index: 1000;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    backdrop-filter: blur(8px);
  }}
  #tooltip .tt-title {{
    font-weight: 700;
    font-size: 13px;
    margin-bottom: 4px;
    border-bottom: 1px solid rgba(255,255,255,0.15);
    padding-bottom: 4px;
  }}
  #tooltip .tt-row {{
    display: flex;
    justify-content: space-between;
    gap: 12px;
  }}
  #tooltip .tt-label {{ color: #94A3B8; }}
  #tooltip .tt-value {{ font-weight: 500; font-family: monospace; }}
  #tooltip .tt-status-ok {{ color: #34D399; }}
  #tooltip .tt-status-warning {{ color: #FBBF24; }}
  #tooltip .tt-status-error {{ color: #F87171; }}

  /* Legend */
  .legend {{
    display: flex;
    gap: 16px;
    justify-content: center;
    padding: 8px 0 4px;
    flex-wrap: wrap;
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    color: #64748B;
    font-family: system-ui, sans-serif;
  }}
  .legend-dot {{
    width: 10px; height: 10px;
    border-radius: 2px;
  }}
</style>
</head>
<body>
<div class="container">
  {svg}
  <div id="tooltip"></div>
</div>
<div class="legend">
  {''.join(f'<span class="legend-item"><span class="legend-dot" style="background:{COLORS[m]["fill"]}"></span>{COLORS[m]["label"]} ({m})</span>' for m in SWIMLANE_ORDER)}
  <span class="legend-item"><svg width="14" height="10"><polygon points="7,0 14,5 7,10 0,5" fill="#F59E0B"/></svg>Warning</span>
  <span class="legend-item"><svg width="14" height="14"><line x1="2" y1="2" x2="12" y2="12" stroke="#DC2626" stroke-width="2"/><line x1="12" y1="2" x2="2" y2="12" stroke="#DC2626" stroke-width="2"/></svg>Interrupt</span>
</div>
<script>
(function() {{
  const tooltip = document.getElementById('tooltip');
  const bars = document.querySelectorAll('.span-bar');

  bars.forEach(bar => {{
    bar.addEventListener('mouseenter', function(e) {{
      try {{
        const d = JSON.parse(this.getAttribute('data-hover'));
        const statusClass = 'tt-status-' + (d.status || 'ok');
        let html = '<div class="tt-title">' + d.module + ': ' + d.name + '</div>';
        html += '<div class="tt-row"><span class="tt-label">Status</span><span class="tt-value ' + statusClass + '">' + d.status + '</span></div>';
        html += '<div class="tt-row"><span class="tt-label">Input tokens</span><span class="tt-value">' + d.input_tokens.toLocaleString() + '</span></div>';
        html += '<div class="tt-row"><span class="tt-label">Output tokens</span><span class="tt-value">' + d.output_tokens.toLocaleString() + '</span></div>';
        html += '<div class="tt-row"><span class="tt-label">Duration</span><span class="tt-value">' + d.duration_ms + ' ms</span></div>';
        if (d.zt) html += '<div class="tt-row"><span class="tt-label">z_t</span><span class="tt-value ' + (d.zt === 'Warning' ? 'tt-status-warning' : d.zt === 'Error' ? 'tt-status-error' : 'tt-status-ok') + '">' + d.zt + '</span></div>';
        if (d.notes) html += '<div class="tt-row"><span class="tt-label">Notes</span><span class="tt-value">' + d.notes + '</span></div>';
        tooltip.innerHTML = html;
        tooltip.style.display = 'block';
      }} catch(e) {{}}
    }});
    bar.addEventListener('mousemove', function(e) {{
      const rect = this.closest('.container').getBoundingClientRect();
      let x = e.clientX - rect.left + 15;
      let y = e.clientY - rect.top - 10;
      if (x + {TOOLTIP_W} > {width}) x = x - {TOOLTIP_W} - 30;
      tooltip.style.left = x + 'px';
      tooltip.style.top = y + 'px';
    }});
    bar.addEventListener('mouseleave', function() {{
      tooltip.style.display = 'none';
    }});
  }});
}})();
</script>
</body>
</html>"""

    return full_html

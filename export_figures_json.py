#!/usr/bin/env python3
"""Export all Plotly figures as JSON for Streamlit app."""
import sys, json
from pathlib import Path

# Add parent to path to import generator
sys.path.insert(0, str(Path(__file__).parent.parent / "process_viz_v2"))
from generate_process_figures import (
    generate_all_bundles, plot_p1_causal_timeline, plot_p2_token_asymmetry,
    plot_p3_time_occupancy, plot_p4_butterfly, plot_p5_module_roi,
    plot_p6_waterfall, plot_p7_gallery, plot_p8_domain_radar,
)

SEED = 20260327
OUT = Path(__file__).parent / "figures"
OUT.mkdir(exist_ok=True)

bundles = generate_all_bundles(SEED)

# Select cases
pid_cases = [b for b in bundles if "pid" in b.get("run_id", "").lower()
             and b.get("is_success") and b.get("iterations", 1) >= 2]
hero = pid_cases[0] if pid_cases else bundles[0]
waterfall_case = max(
    [b for b in bundles if b.get("is_success") and b.get("iterations", 1) >= 3],
    key=lambda b: b.get("iterations", 1), default=hero,
)

figures = {
    "p1_causal_timeline": plot_p1_causal_timeline(hero),
    "p2_token_asymmetry": plot_p2_token_asymmetry(hero),
    "p3_time_occupancy": plot_p3_time_occupancy(bundles),
    "p4_butterfly_comparison": plot_p4_butterfly(bundles),
    "p5_module_roi": plot_p5_module_roi(bundles),
    "p6_token_waterfall": plot_p6_waterfall(waterfall_case),
    "p7_multi_case_gallery": plot_p7_gallery(bundles),
    "p8_domain_radar": plot_p8_domain_radar(bundles),
}

for name, fig in figures.items():
    # Strip template to avoid cross-version Plotly incompatibility
    fig.update_layout(template=None)
    path = OUT / f"{name}.json"
    path.write_text(fig.to_json(), encoding="utf-8")
    print(f"  Exported: {path.name} ({path.stat().st_size // 1024}KB)")

# Also save trace data summary
summary = []
for b in bundles:
    summary.append(dict(
        run_id=b["run_id"], problem_id=b["problem_id"], domain=b["domain"],
        is_success=b["is_success"], iterations=b["iterations"],
        total_tokens=b.get("token_totals", {}).get("total_tokens", 0),
        difficulty=b.get("difficulty", ""),
    ))
(OUT / "bundles_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

# Save hero trace bundle for custom SVG renderer
(OUT / "trace_bundle_hero.json").write_text(json.dumps(hero, indent=2, default=str), encoding="utf-8")
print(f"  Exported: trace_bundle_hero.json")

print(f"\nDone! {len(figures)} figures + hero bundle exported to {OUT}")

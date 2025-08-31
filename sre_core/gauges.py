# sre_core/gauges.py
from __future__ import annotations
import math
from typing import Dict, List, Tuple, Optional

import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

# ---------- Completion math (pure, no Streamlit) ----------

def stage_completion_from(
    maturity_items: List[dict],
    responses_all: Dict[str, Dict[str, Dict[str, str]]],
    product: str,
    levels: List[str],
) -> Dict[str, float]:
    """% Completed per stage for a product."""
    prod_res = responses_all.get(product, {}) or {}

    by_stage: Dict[str, List[dict]] = {}
    for it in maturity_items:
        by_stage.setdefault(it["Stage"], []).append(it)

    out: Dict[str, float] = {}
    for stage, caps in by_stage.items():
        total = done = 0
        for it in caps:
            cap_res = prod_res.get(it["Capability"], {}) or {}
            for lvl in levels:
                total += 1
                if cap_res.get(lvl, "Not achieved") == "Completed":
                    done += 1
        out[stage] = (done / total) if total else 0.0
    return out

# ---------- Donut (unchanged/simple) ----------

def _half_donut(ax, pct: float, r: float = 1.0, width: float = 0.28) -> None:
    """Draw a half donut with a filled arc for pct, rotated to top.

    Orientation and direction:
    - Background semicircle spans the TOP half (0°..180°).
    - Filled arc grows from LEFT (0%) to RIGHT (100%) along the top.
    """
    pct = max(0.0, min(1.0, float(pct)))
    # background half (TOP): 0°..180° (right to left across the top)
    ax.add_patch(Wedge((0, 0), r, 0, 180, width=width, facecolor="#eeeeee", edgecolor="none"))
    # color by threshold: red <40%, yellow <80%, green >=80%
    color = "#d9534f" if pct < 0.4 else ("#f0ad4e" if pct < 0.8 else "#5cb85c")
    # filled arc grows LEFT -> RIGHT along top: 180° - span .. 180°
    span = pct * 180.0
    ax.add_patch(Wedge((0, 0), r, 180 - span, 180, width=width, facecolor=color, edgecolor="none"))
    # percentage text
    ax.text(0, 0, f"{pct * 100:.1f}%", ha="center", va="center", fontsize=11)
    # ensure a square, centered drawing area so donuts aren't squashed or off-center
    ax.set_xlim(-r, r)
    ax.set_ylim(-r, r)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

def grid_from_completion(
    completion: Dict[str, float],
    cols: int = 5,
    title: str = "Stage Completion Overview",
    show: bool = True,
):
    """Render a grid of half-donuts. Returns (fig, axes)."""
    stages = sorted(completion.keys())
    n = len(stages)
    cols = max(1, cols)
    rows = (n + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 3.2, rows * 3.0))
    if rows == 1 and cols == 1:
        axes = [[axes]]
    elif rows == 1:
        axes = [axes]
    elif cols == 1:
        axes = [[ax] for ax in axes]

    idx = 0
    for r in range(rows):
        for c in range(cols):
            ax = axes[r][c]
            if idx >= n:
                ax.axis("off")
                continue
            stg = stages[idx]
            _half_donut(ax, completion[stg])
            ax.set_title(stg, fontsize=11, pad=10)
            idx += 1

    fig.suptitle(title, fontsize=16, y=0.98)
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])

    if show:
        try:
            import streamlit as st
            st.pyplot(fig, use_container_width=True, clear_figure=True)
        except Exception:
            pass

    return fig, axes

# ---------- Ring chart (only label rotation adjusted) ----------

def ring_maturity_by_stage(
    stages: List[str],
    levels: List[str],
    achieved_map: Optional[Dict[Tuple[str, str], bool]] = None,
    *,
    # Back-compat alias: some callers pass `filled={(stage, lvl): fraction}`
    filled: Optional[Dict[Tuple[str, str], float]] = None,
    # New: explicit tri-state status per level: 'not'|'partial'|'completed'
    status_map: Optional[Dict[Tuple[str, str], str]] = None,
    # Optional per-stage extra label rotation (in degrees)
    label_rotation_overrides: Optional[Dict[str, float]] = None,
    figsize: Optional[Tuple[float, float]] = None,
    r0: float = 1.2,         # inner radius of first level band
    step: float = 0.20,      # thickness of each level band
    band_gap: float = 0.04,  # gap between level bands
    sector: float = math.radians(30),  # angle per stage sector
    gap: float = math.radians(6),      # gap between sectors
    colors: Tuple[str, str] = ("#2094f3", "#eaeaea"),
    title: Optional[str] = "Identification of the degree of the implementation\n(Maturity by Stage)",
):
    """
    Sunburst-like ring: each stage is a sector; each level a concentric band.
    Accepts either `achieved_map[(stage, level)] -> bool` or
    `filled[(stage, level)] -> float` (treated as achieved if > 0).
    Returns only the Matplotlib figure for convenient use with Streamlit.
    """
    # Normalize data source into a tri-state map for coloring
    # Priority: status_map -> achieved_map -> filled
    tri: Dict[Tuple[str, str], str] = {}
    if status_map:
        for k, v in status_map.items():
            vv = str(v).lower()
            tri[k] = vv if vv in {"not", "partial", "completed"} else ("completed" if vv in {"true", "1", "yes"} else "not")
    elif achieved_map is not None:
        tri = {k: ("completed" if bool(v) else "not") for k, v in achieved_map.items()}
    elif filled is not None:
        tri = {k: ("completed" if float(v) >= 0.999 else ("partial" if float(v) > 0.0 else "not")) for k, v in filled.items()}
    else:
        # default all to 'not'
        for st in stages:
            for lv in levels:
                tri[(st, lv)] = "not"
    total = sector + gap
    # Polar axes where theta=0 at +x, increasing CCW.
    fig, ax = plt.subplots(subplot_kw=dict(polar=True), figsize=figsize or (9, 9))
    ax.set_axis_off()

    # Colors
    col_bg = colors[1]
    col_completed = colors[0]
    # Partial uses the same blue hue with transparency to keep color consistent
    col_partial = colors[0]

    # Draw sectors
    for i, stage in enumerate(stages):
        start = i * total
        stop = start + sector

        # draw each level band once according to its status
        for li, lvl in enumerate(levels):
            r_inner = r0 + li * (step + band_gap)
            status = tri.get((stage, lvl), "not")
            if status == "not":
                # light grey background only when not achieved
                ax.bar(
                    x=start + sector / 2.0, height=step, width=sector,
                    bottom=r_inner, align="center",
                    color=col_bg, edgecolor="white", linewidth=1.0
                )
            elif status == "completed":
                # full-width bold blue
                ax.bar(
                    x=start + sector / 2.0, height=step, width=sector,
                    bottom=r_inner, align="center",
                    color=col_completed, edgecolor="white", linewidth=1.0, alpha=1.0
                )
            else:
                # full-width soft blue (same hue, lower alpha)
                ax.bar(
                    x=start + sector / 2.0, height=step, width=sector,
                    bottom=r_inner, align="center",
                    color=col_partial, edgecolor="white", linewidth=1.0, alpha=0.35
                )

    # --- Stage labels: tangent + upright (THIS IS THE ONLY CHANGE) ---
    r_label = r0 + len(levels) * (step + band_gap) + 0.12
    label_rot_over = label_rotation_overrides or {}
    for i, stage in enumerate(stages):
        ang = (i * (sector + gap) + sector / 2.0)          # radians
        deg = math.degrees(ang)
        rot = deg - 90                                     # tangent
        if 90 < deg < 270:
            rot += 180                                     # keep upright
        # apply any explicit override (degrees)
        rot += float(label_rot_over.get(stage, 0.0))

        # Anchor label so its bottom edge faces the diagram center consistently
        ax.text(
            ang, r_label, stage,
            rotation=rot, rotation_mode="anchor",
            ha="center", va="baseline",
            fontsize=12, color="#222", clip_on=False,
        )

    if title:
        fig.suptitle(title, fontsize=18, y=0.96)
    fig.tight_layout(rect=[0, 0.00, 1, 0.94])
    return fig

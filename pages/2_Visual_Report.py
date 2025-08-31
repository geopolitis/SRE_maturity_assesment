# pages/2_Visual_Report.py
from __future__ import annotations

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

from sre_core.init_app import init_app
from sre_core import scoring, plotting
from sre_core.constants import LEVELS
from sre_core.gauges import (
    stage_completion_from,
    grid_from_completion,
    ring_maturity_by_stage,
)

# No sidebar controls on report pages
init_app(show_sidebar_controls=False)

st.title("SRE Maturity Visual Report")

# ---------- Data guards ----------
cap_df = st.session_state.get("cap_df")
if cap_df is None:
    st.info("No capabilities loaded. Go to the Assessment page to upload a CSV.")
    st.stop()

df = scoring.build_df(st.session_state.maturity_items, st.session_state.responses_all)
if df.empty:
    st.info("No responses yet.")
    st.stop()

# ---------- Radar sizing (match PDF style) ----------
# We'll compute a shared adaptive size based on capability count (same as PDF)
# but let users increase it via an optional slider cap.
slider_size = st.sidebar.slider("Max radar size (inches)", min_value=6, max_value=14, value=10)

# ---------- Radar by Stage ----------
radar_stage = df.groupby(["Product", "Stage"])["Score"].mean().reset_index()
labels_stage = sorted(radar_stage["Stage"].unique().tolist())

# Determine shared size using capability count (like PDF)
labels_cap_for_size = df["Capability"].unique().tolist()
cap_count = max(1, len(labels_cap_for_size))
shared_size = (
    7.5 if cap_count <= 24 else
    9.5 if cap_count <= 48 else
    12.5 if cap_count <= 80 else
    14.0
)
radar_size = min(max(shared_size, 6.0), float(slider_size))

fig1, ax1 = plt.subplots(figsize=(radar_size, radar_size), subplot_kw=dict(polar=True))
for prod in radar_stage["Product"].unique():
    vals = (
        radar_stage[radar_stage["Product"] == prod]
        .set_index("Stage")
        .reindex(labels_stage)["Score"]
        .fillna(0)
        .tolist()
    )
    plotting.plot_radar(ax1, labels_stage, vals, label=prod, y_max=len(LEVELS))
ax1.set_title("Average score by Stage", pad=26, fontsize=12)
# Legend centered above, hide when only one series
handles, labels = ax1.get_legend_handles_labels()
if len(handles) > 1:
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2, fontsize=8, frameon=False)
elif ax1.legend_:
    ax1.legend_.remove()

# Axis-aligned labels (match PDF)
def _align_polar_labels(ax):
    ticks = ax.get_xticks()
    labels = ax.get_xticklabels()
    for ang, lab in zip(ticks, labels):
        deg = (np.degrees(ang) % 360)
        rot = deg
        ha = 'left'
        if 90 < deg < 270:
            rot = deg + 180
            ha = 'right'
        lab.set_rotation(rot)
        lab.set_rotation_mode('anchor')
        lab.set_ha(ha)
        lab.set_va('center')

stage_fs = 9 if len(labels_stage) <= 10 else 8 if len(labels_stage) <= 16 else 7
ax1.tick_params(axis='x', labelsize=stage_fs, pad=6)
_align_polar_labels(ax1)
fig1.tight_layout(pad=1.0, rect=[0.02, 0.02, 0.98, 0.84])

def _render_fig(fig):
    try:
        st.pyplot(fig, width='stretch')
    except TypeError:
        st.pyplot(fig, use_container_width=True, clear_figure=True)

with st.expander("Radar by Stage", expanded=True):
    _render_fig(fig1)

# ---------- Radar by Capability ----------
radar_cap = df.groupby(["Product", "Capability"])["Score"].mean().reset_index()
labels_cap = sorted(radar_cap["Capability"].unique().tolist())

fig2, ax2 = plt.subplots(figsize=(radar_size, radar_size), subplot_kw=dict(polar=True))
for prod in radar_cap["Product"].unique():
    vals = (
        radar_cap[radar_cap["Product"] == prod]
        .set_index("Capability")
        .reindex(labels_cap)["Score"]
        .fillna(0)
        .tolist()
    )
    plotting.plot_radar(ax2, labels_cap, vals, label=prod, y_max=len(LEVELS))
ax2.set_title("Average score by Capability", pad=26, fontsize=12)
handles2, labels2 = ax2.get_legend_handles_labels()
if len(handles2) > 1:
    ax2.legend(loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2, fontsize=8, frameon=False)
elif ax2.legend_:
    ax2.legend_.remove()

cap_count2 = max(1, len(labels_cap))
cap_fs = 9 if cap_count2 <= 12 else 8 if cap_count2 <= 24 else 7 if cap_count2 <= 36 else 6 if cap_count2 <= 60 else 5
ax2.tick_params(axis='x', labelsize=cap_fs, pad=6)
_align_polar_labels(ax2)
fig2.tight_layout(pad=1.0, rect=[0.02, 0.02, 0.98, 0.84])

with st.expander("Radar by Capability", expanded=True):
    _render_fig(fig2)

# ---------- Stage Completion Half-Donuts ----------
st.markdown("### Stage Completion Overview")

selected_product = st.session_state.get("selected_product")
if not selected_product:
    st.info("No product selected. Please select a product in the Assessment page.")
else:
    completion = stage_completion_from(
        st.session_state.maturity_items,
        st.session_state.responses_all,
        selected_product,
        LEVELS,
    )
    # Avoid double-render inside grid_from_completion by disabling auto-show
    fig_g, _axes = grid_from_completion(completion, cols=5, show=False)
    _render_fig(fig_g)

# ---------- Circular “degree of implementation” chart ----------
st.markdown("### Degree of Implementation (Maturity by Stage)")

if selected_product:
    # Build tri-state status per (stage, level): 'not' | 'partial' | 'completed'
    status_map = {}
    prod_res = (st.session_state.responses_all or {}).get(selected_product, {}) or {}
    items = st.session_state.maturity_items or []

    by_stage = {}
    for it in items:
        by_stage.setdefault(it["Stage"], []).append(it)

    for stage, caps in by_stage.items():
        for lvl in LEVELS:
            total = 0
            completed = 0
            partial = 0
            for it in caps:
                cap_res = prod_res.get(it["Capability"], {}) or {}
                status = cap_res.get(lvl, "Not achieved")
                total += 1
                if status == "Completed":
                    completed += 1
                elif status == "Partially achieved":
                    partial += 1
            if total and completed == total:
                status_map[(stage, lvl)] = "completed"
            elif (completed > 0) or (partial > 0):
                status_map[(stage, lvl)] = "partial"
            else:
                status_map[(stage, lvl)] = "not"

    stages_order = sorted(by_stage.keys())

    ring_size = st.sidebar.slider("Circular chart size (inches)", 8, 14, 10)
    # Rotate specific labels by +190 degrees (previous +100 needed +90 more)
    label_overrides = {"Develop": 190, "Observe": 190, "Secure": 190, "Test": 190, "tests": 190, "Tests": 190}
    fig_ring = ring_maturity_by_stage(
        stages=stages_order,
        levels=LEVELS,
        status_map=status_map,
        label_rotation_overrides=label_overrides,
        figsize=(ring_size, ring_size),
    )
    with st.expander("Identification of the degree of the implementation (Maturity by Stage)", expanded=True):
        _render_fig(fig_ring)

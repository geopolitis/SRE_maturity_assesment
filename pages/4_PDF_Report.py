# pages/4_PDF_Report.py
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

from sre_core.init_app import init_app
from sre_core import scoring, plotting, pdf_report
from sre_core.constants import LEVELS

init_app(show_sidebar_controls=False)
st.title("SRE Maturity PDF Report")

# Guards
if not getattr(st.session_state, "maturity_items", None):
    st.info("No capabilities loaded. Go to the Assessment page to upload a CSV.")
    st.stop()
if not getattr(st.session_state, "responses_all", None):
    st.info("No responses yet. Fill in the Assessment first.")
    st.stop()

product = st.session_state.get("selected_product")
if not product:
    st.info("Select a product in the Assessment page.")
    st.stop()

df = scoring.build_df(st.session_state.maturity_items, st.session_state.responses_all)
if df.empty:
    st.info("No responses yet.")
    st.stop()

pdf_df = df[df["Product"] == product]
if pdf_df.empty:
    st.info(f"No responses found for product '{product}'.")
    st.stop()

# Radar by Stage
stages = sorted(pdf_df["Stage"].unique().tolist())
stage_vals = [
    float(pdf_df[pdf_df["Stage"] == s]["Score"].mean()) if not pdf_df[pdf_df["Stage"] == s].empty else 0.0
    for s in stages
]
title_fs_stage = 10
title_pad_stage = 16
title_fs_cap = 12
title_pad_cap = 28

# Determine a shared size for both radars (symmetry)
cap_count = max(1, len(pdf_df["Capability"].unique().tolist()))
shared_size = (
    7.5 if cap_count <= 24 else
    9.5 if cap_count <= 48 else
    12.5 if cap_count <= 80 else
    14.0
)

fig1, ax1 = plt.subplots(figsize=(shared_size, shared_size), subplot_kw=dict(polar=True))
plotting.plot_radar(ax1, stages if stages else ["N/A"], stage_vals if stage_vals else [0.0], label="Stage")
ax1.set_title("Average score by Stage", pad=title_pad_stage, fontsize=title_fs_stage)
# Legend placement and tick label sizing for readability
if stages:
    handles, labels = ax1.get_legend_handles_labels()
    if len(handles) > 1:
        ax1.legend(loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2, fontsize=8, frameon=False)
    elif ax1.legend_:
        ax1.legend_.remove()
stage_fs = 9 if len(stages) <= 10 else 8 if len(stages) <= 16 else 7
ax1.tick_params(axis='x', labelsize=stage_fs, pad=6)

# Align label rotation to their axis angle (upright)
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

_align_polar_labels(ax1)
# Reserve extra top space for the title/legend
fig1.tight_layout(pad=1.0, rect=[0.02, 0.02, 0.98, 0.92])
def _render_fig(fig):
    try:
        st.pyplot(fig, width='stretch')
    except TypeError:
        st.pyplot(fig, use_container_width=True)

_render_fig(fig1)

# Radar by Capability
caps = sorted(pdf_df["Capability"].unique().tolist())
cap_vals = [
    float(pdf_df[pdf_df["Capability"] == c]["Score"].mean()) if not pdf_df[pdf_df["Capability"] == c].empty else 0.0
    for c in caps
]
cap_count = max(1, len(caps))
fig2, ax2 = plt.subplots(figsize=(shared_size, shared_size), subplot_kw=dict(polar=True))
plotting.plot_radar(ax2, caps if caps else ["N/A"], cap_vals if cap_vals else [0.0], label="Capability")
ax2.set_title("Average score by Capability", pad=title_pad_cap, fontsize=title_fs_cap)
if caps:
    handles, labels = ax2.get_legend_handles_labels()
    if len(handles) > 1:
        ax2.legend(loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2, fontsize=8, frameon=False)
    elif ax2.legend_:
        ax2.legend_.remove()
cap_fs = 9 if cap_count <= 12 else 8 if cap_count <= 24 else 7 if cap_count <= 36 else 6 if cap_count <= 60 else 5
ax2.tick_params(axis='x', labelsize=cap_fs, pad=6)

_align_polar_labels(ax2)
fig2.tight_layout(pad=1.0, rect=[0.02, 0.02, 0.98, 0.82])
_render_fig(fig2)

# Build + download (spinner in the sidebar bottom)
with st.sidebar:
    st.markdown("---")
    st.caption("Report")
    with st.spinner("Building PDF report…"):
        tmp_pdf = pdf_report.generate_pdf(
            product=product,
            maturity_items=st.session_state.maturity_items,
            responses=st.session_state.responses_all.get(product, {}),
            fig_stage=fig1,
            fig_cap=fig2,
        )
        data = tmp_pdf.read()

    st.download_button(
        "Download PDF Report",
        data=data,
        file_name=f"{product}_maturity_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

# Cleanup
plt.close(fig1)
plt.close(fig2)

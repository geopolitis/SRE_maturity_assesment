# pages/4_PDF_Report.py
import streamlit as st
import matplotlib.pyplot as plt

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
fig1, ax1 = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
plotting.plot_radar(ax1, stages if stages else ["N/A"], stage_vals if stage_vals else [0.0], label="Stage")
ax1.set_title("Average score by Stage")
if stages:
    ax1.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))
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
fig2, ax2 = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
plotting.plot_radar(ax2, caps if caps else ["N/A"], cap_vals if cap_vals else [0.0], label="Capability")
ax2.set_title("Average score by Capability")
if caps:
    ax2.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))
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

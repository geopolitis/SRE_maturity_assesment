import streamlit as st
import matplotlib.pyplot as plt
from sre_core.init_app import init_app
from sre_core import scoring, plotting, pdf_report
from sre_core.constants import LEVELS

init_app(show_sidebar_controls=False)

st.title("SRE Maturity PDF Report")

if st.session_state.cap_df is None:
    st.info("No capabilities loaded. Go to the Assessment page to upload a CSV.")
else:
    df = scoring.build_df(st.session_state.maturity_items, st.session_state.responses_all)
    if df.empty:
        st.info("No responses yet.")
    else:
        # Build figures like Visual Report
        radar_stage = df.groupby(["Product", "Stage"])["Score"].mean().reset_index()
        labels_stage = sorted(radar_stage["Stage"].unique().tolist())
        fig1, ax1 = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        for prod in radar_stage["Product"].unique():
            vals = (
                radar_stage[radar_stage["Product"] == prod]
                .set_index("Stage")
                .reindex(labels_stage)["Score"]
                .fillna(0)
                .tolist()
            )
            plotting.plot_radar(ax1, labels_stage, vals, label=prod, y_max=len(LEVELS))
        ax1.set_title("Maturity by Stage"); ax1.legend(loc="upper right")

        radar_cap = df.groupby(["Product", "Capability"])["Score"].mean().reset_index()
        labels_cap = sorted(radar_cap["Capability"].unique().tolist())
        fig2, ax2 = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        for prod in radar_cap["Product"].unique():
            vals = (
                radar_cap[radar_cap["Product"] == prod]
                .set_index("Capability")
                .reindex(labels_cap)["Score"]
                .fillna(0)
                .tolist()
            )
            plotting.plot_radar(ax2, labels_cap, vals, label=prod, y_max=len(LEVELS))
        ax2.set_title("Maturity by Capability"); ax2.legend(loc="upper right")

        tmp_pdf = pdf_report.generate_pdf(
            product=st.session_state.selected_product,
            maturity_items=st.session_state.maturity_items,
            responses=st.session_state.responses_all.get(st.session_state.selected_product, {}),
            fig_stage=fig1,
            fig_cap=fig2,
        )

        st.sidebar.download_button(
            "Download PDF Report",
            data=open(tmp_pdf.name, "rb").read(),
            file_name=f"{st.session_state.selected_product}_maturity_report.pdf",
            mime="application/pdf",
        )

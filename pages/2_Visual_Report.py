# pages/2_Visual_Report.py
import streamlit as st
import matplotlib.pyplot as plt

from sre_core.init_app import init_app
from sre_core import scoring, plotting
from sre_core.constants import LEVELS
from sre_core.gauges import (
    wrap_label,
    make_semi_donut,
    stage_completion_for_product,
)

# No sidebar controls on report pages
init_app(show_sidebar_controls=False)

st.title("SRE Maturity Visual Report")

# ---------- Data ----------
cap_df = st.session_state.get("cap_df", None)
if cap_df is None:
    st.info("No capabilities loaded. Go to the Assessment page to upload a CSV.")
    st.stop()

df = scoring.build_df(st.session_state.maturity_items, st.session_state.responses_all)
if df.empty:
    st.info("No responses yet.")
    st.stop()

# ---------- Table ----------
st.dataframe(df, use_container_width=True)

# ---------- Radar by Stage ----------
radar_stage = df.groupby(["Product", "Stage"])["Score"].mean().reset_index()
labels_stage = sorted(radar_stage["Stage"].unique().tolist())
fig1, ax1 = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
for prod in radar_stage["Product"].unique():
    vals = (
        radar_stage[radar_stage["Product"] == prod]
        .set_index("Stage").reindex(labels_stage)["Score"]
        .fillna(0).tolist()
    )
    plotting.plot_radar(ax1, labels_stage, vals, label=prod, y_max=len(LEVELS))
ax1.set_title("Maturity by Stage")
ax1.legend(bbox_to_anchor=(1.25, 1.1), loc="upper left", fontsize=9)
st.pyplot(fig1, clear_figure=True)

# ---------- Radar by Capability ----------
radar_cap = df.groupby(["Product", "Capability"])["Score"].mean().reset_index()
labels_cap = sorted(radar_cap["Capability"].unique().tolist())
fig2, ax2 = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
for prod in radar_cap["Product"].unique():
    vals = (
        radar_cap[radar_cap["Product"] == prod]
        .set_index("Capability").reindex(labels_cap)["Score"]
        .fillna(0).tolist()
    )
    plotting.plot_radar(ax2, labels_cap, vals, label=prod, y_max=len(LEVELS))
ax2.set_title("Maturity by Capability")
ax2.legend(bbox_to_anchor=(1.25, 1.1), loc="upper left", fontsize=9)
st.pyplot(fig2, clear_figure=True)

# ---------- Semi-donut “clock” gauges ----------
st.markdown("### ⏱ Stage Completion Overview")
selected_product = st.session_state.get("selected_product")
if not selected_product:
    st.warning("No product selected. Please select a product in the Assessment page.")
else:
    completion = stage_completion_for_product(
        selected_product, st.session_state.maturity_items, st.session_state.responses_all
    )
    if completion:
        stages_sorted = sorted(completion.items(), key=lambda x: x[0])
        num_stages = len(stages_sorted)
        num_cols = 5 if num_stages >= 7 else 2
        cols = st.columns(num_cols)

        for idx, (stage, pct) in enumerate(stages_sorted):
            with cols[idx % num_cols]:
                fig = make_semi_donut(stage, pct)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No stages found in the loaded capabilities.")

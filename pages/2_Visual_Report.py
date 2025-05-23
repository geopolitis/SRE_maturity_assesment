# pages/2_Visual_Report.py
import textwrap
import streamlit as st
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from sre_core.init_app import init_app
from sre_core import scoring, plotting
from sre_core.constants import LEVELS

# No sidebar controls on report pages
init_app(show_sidebar_controls=False)

st.title("SRE Maturity Visual Report")

# ---------- Helpers ----------
def wrap_label(label: str, width: int = 18) -> str:
    """Wrap long stage names onto multiple lines for Plotly titles."""
    return "<br>".join(textwrap.wrap(label, width=width)) if label else label

def stage_completion_for_product(product: str) -> dict[str, float]:
    """% complete per stage for selected product, based on saved responses."""
    items = st.session_state.get("maturity_items", [])
    responses_all = st.session_state.get("responses_all", {})
    prod_res = responses_all.get(product, {})

    by_stage = {}
    for it in items:
        by_stage.setdefault(it["Stage"], []).append(it)

    result = {}
    for stage, caps in by_stage.items():
        total = done = 0
        for it in caps:
            cap_res = prod_res.get(it["Capability"], {})
            for lvl in LEVELS:
                total += 1
                if cap_res.get(lvl, "Not achieved") == "Completed":
                    done += 1
        result[stage] = (done / total) if total else 0.0
    return result

def make_semi_donut(title: str, pct_float: float) -> go.Figure:
    """
    Semi-donut gauge built from layered pies.
    - Background bands (0–40 / 40–80 / 80–100) with soft colors
    - Foreground progress arc colored by threshold
    - Big % number centered; wrapped title above
    """
    pct = max(0.0, min(1.0, float(pct_float)))
    pct_val = round(pct * 100, 1)

    # Colors
    band_low   = "#ffefef"   # 0–40
    band_mid   = "#fff6db"   # 40–80
    band_high  = "#edfbea"   # 80–100
    transparent = "rgba(0,0,0,0)"
    bar_color = "red" if pct < 0.4 else ("orange" if pct < 0.8 else "green")

    # --- Background semicircle (bands) ---
    # Values sum to 200 so the last 100 becomes the hidden lower half.
    bg = go.Pie(
        values=[40, 40, 20, 100],
        rotation=180,  # start at 180° to show upper half
        hole=0.70,
        marker=dict(colors=[band_low, band_mid, band_high, transparent]),
        textinfo="none",
        hoverinfo="skip",
        sort=False,
        direction="clockwise",
        showlegend=False,
    )

    # --- Foreground progress arc ---
    fg = go.Pie(
        values=[pct * 100, (1 - pct) * 100, 100],
        rotation=180,
        hole=0.70,
        marker=dict(colors=[bar_color, transparent, transparent]),
        textinfo="none",
        hoverinfo="skip",
        sort=False,
        direction="clockwise",
        showlegend=False,
    )

    fig = go.Figure(data=[bg, fg])
    fig.update_layout(
        height=230,
        margin=dict(t=38, b=8, l=8, r=8),
        annotations=[
            # Title (wrapped) above the gauge
            dict(
                text=wrap_label(title, 20),
                x=0.5, y=1.15, xref="paper", yref="paper",
                showarrow=False, align="center",
                font=dict(size=12)
            ),
            # Big % in the center
            dict(
                text=f"{pct_val:g}%",
                x=0.5, y=0.48, xref="paper", yref="paper",
                showarrow=False, align="center",
                font=dict(size=20)
            ),
            # Axis ticks (0 | 50 | 100) as tiny labels
            dict(text="0",   x=0.05, y=0.08, xref="paper", yref="paper", showarrow=False, font=dict(size=10, color="#555")),
            dict(text="50",  x=0.50, y=0.13, xref="paper", yref="paper", showarrow=False, font=dict(size=10, color="#555")),
            dict(text="100", x=0.95, y=0.08, xref="paper", yref="paper", showarrow=False, font=dict(size=10, color="#555")),
        ],
        # Hide pie legends; keep a clean look
        showlegend=False,
    )
    return fig

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
        .set_index("Stage")
        .reindex(labels_stage)["Score"]
        .fillna(0)
        .tolist()
    )
    plotting.plot_radar(ax1, labels_stage, vals, label=prod, y_max=len(LEVELS))
ax1.set_title("Maturity by Stage")
# Move legend outside to avoid overlap
ax1.legend(bbox_to_anchor=(1.25, 1.1), loc="upper left", fontsize=9)
st.pyplot(fig1, clear_figure=True)

# ---------- Radar by Capability ----------
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
ax2.set_title("Maturity by Capability")
ax2.legend(bbox_to_anchor=(1.25, 1.1), loc="upper left", fontsize=9)
st.pyplot(fig2, clear_figure=True)

# ---------- Semi-donut “clock” gauges ----------
st.markdown("### ⏱ Stage Completion Overview")

selected_product = st.session_state.get("selected_product")
if not selected_product:
    st.warning("No product selected. Please select a product in the Assessment page.")
else:
    completion = stage_completion_for_product(selected_product)
    if completion:
        # Sort for predictable layout; choose 3 columns for many stages, else 2
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

import streamlit as st
from sre_core.constants import LEVELS, SUB_LEVELS
from sre_core.persistence import save_responses
from sre_core.init_app import init_app

# Initialise app without extra sidebar controls
init_app(show_sidebar_controls=True)

st.title("SRE Maturity Assessment")

# Helpers
def get_status(product: str, capability: str, level: str) -> str:
    return (
        st.session_state.responses_all.get(product, {})
        .get(capability, {})
        .get(level, "Not achieved")
    )

def set_status(product: str, capability: str, level: str, value: str):
    st.session_state.responses_all.setdefault(product, {}).setdefault(capability, {})[
        level
    ] = value
    save_responses(st.session_state.responses_all)

def wkey(product: str, stage: str, cap: str, lvl: str) -> str:
    """Unique widget key."""
    return f"{product}::{stage}::{cap}::{lvl}"

def pct_completed_for_stage(prod: str, stage_name: str, items_by_stage: dict) -> float:
    """Calculate % completed for a given stage from saved data."""
    total = done = 0
    prod_res = st.session_state.responses_all.get(prod, {})
    for it in items_by_stage.get(stage_name, []):
        cap_res = prod_res.get(it["Capability"], {})
        for lvl in LEVELS:
            total += 1
            if cap_res.get(lvl, "Not achieved") == "Completed":
                done += 1
    return (done / total) if total else 0.0

# Ensure we have loaded capabilities and product
product = st.session_state.get("selected_product", None)
items = st.session_state.get("maturity_items", [])

if not items:
    st.warning("No capabilities loaded. Please upload capabilities data on the Assessment page.")
    st.stop()

if not product:
    st.warning("No product selected. Please select a product in the Assessment page.")
    st.stop()

# Group items by Stage
by_stage = {}
for it in items:
    by_stage.setdefault(it["Stage"], []).append(it)

# Tabs for each stage
tabs = st.tabs(sorted(by_stage.keys()))

for stage_name, tab in zip(sorted(by_stage.keys()), tabs):
    with tab:
        # Progress bar for this stage (initial)
        pct = pct_completed_for_stage(product, stage_name, by_stage)
        prog_ph = st.progress(pct, text=f"{int(pct*100)}% Completed")

        # Render all capabilities in this stage
        for it in by_stage[stage_name]:
            cap = it["Capability"]
            st.markdown(f"**{cap}**")

            # Show descriptions in expander
            with st.expander("Level descriptions", expanded=False):
                for lvl in LEVELS:
                    st.markdown(f"- **{lvl}**: {it[lvl]}")

            # Level radio buttons
            for lvl in LEVELS:
                prev = get_status(product, cap, lvl)
                key = wkey(product, stage_name, cap, lvl)
                choice = st.radio(
                    label=f"{lvl} status",
                    options=SUB_LEVELS,
                    index=SUB_LEVELS.index(prev) if prev in SUB_LEVELS else 0,
                    key=key,
                    horizontal=True,
                )
                if choice != prev:
                    set_status(product, cap, lvl, choice)

            st.markdown("---")

        # Refresh stage progress bar after rendering all capabilities
        pct = pct_completed_for_stage(product, stage_name, by_stage)
        prog_ph.progress(pct, text=f"{int(pct*100)}% Completed")

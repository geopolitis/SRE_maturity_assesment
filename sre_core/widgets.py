import streamlit as st
from .constants import LEVELS, SUB_LEVELS

def widget_key(prod: str, row_idx: int, level: str) -> str:
    return f"w::{prod}::{row_idx}::{level}"

def assessment_ui(selected_product: str, maturity_items, responses_for_product: dict):
    for idx, item in enumerate(maturity_items):
        cap, stage = item["Capability"], item["Stage"]
        st.markdown("---")
        st.markdown(f"**{stage} ➜ {cap}**")
        with st.expander("Level descriptions"):
            for lvl in LEVELS:
                st.markdown(f"- **{lvl}**: {item[lvl]}")
        prev = responses_for_product.get(cap, {})
        lvl_statuses = {}
        for lvl in LEVELS:
            default = prev.get(lvl, "Not achieved")
            st.markdown(f'<span style="font-weight:bold; font-size:1.1em">{lvl}</span> status',
                        unsafe_allow_html=True)
            status = st.radio(
                label=" ",
                options=SUB_LEVELS,
                index=SUB_LEVELS.index(default) if default in SUB_LEVELS else 0,
                key=widget_key(selected_product, idx, lvl),
                horizontal=True,
            )
            lvl_statuses[lvl] = status
        responses_for_product[cap] = lvl_statuses
    return responses_for_product

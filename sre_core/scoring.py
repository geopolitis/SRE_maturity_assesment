import pandas as pd
import streamlit as st
from .constants import LEVELS, SUB_LEVEL_SCORES

@st.cache_data(show_spinner=False)
def build_df(maturity_items, responses_all: dict) -> pd.DataFrame:
    rows = []
    for prod, answers in responses_all.items():
        for item in maturity_items:
            cap, stage = item["Capability"], item["Stage"]
            statuses = answers.get(cap, {})
            score = sum(SUB_LEVEL_SCORES.get(statuses.get(lvl,"Not achieved"), 0) for lvl in LEVELS)
            row = {"Product": prod, "Stage": stage, "Capability": cap, "Score": score}
            for lvl in LEVELS:
                row[lvl] = statuses.get(lvl, "Not achieved")
            rows.append(row)
    return pd.DataFrame(rows)

import pandas as pd
import streamlit as st
from .constants import REQUIRED_COLUMNS

def _normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: c.strip() for c in df.columns})
    mapping = {}
    for c in df.columns:
        low = c.strip().lower().replace("_", " ")
        if low in {"next-gen (2025+)", "next gen (2025+)", "next-gen 2025+", "next gen 2025+", "next gen", "next-gen"}:
            mapping[c] = "Next-Gen (2025+)"
        elif low == "stage": mapping[c] = "Stage"
        elif low == "capability": mapping[c] = "Capability"
        elif low == "beginner": mapping[c] = "Beginner"
        elif low == "intermediate": mapping[c] = "Intermediate"
        elif low == "advanced": mapping[c] = "Advanced"
        elif low == "expert": mapping[c] = "Expert"
    return df.rename(columns=mapping)

def _validate_columns(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Expected: {REQUIRED_COLUMNS}")

@st.cache_data(show_spinner=False)
def load_capabilities(uploaded_or_path) -> pd.DataFrame:
    try:
        df = pd.read_csv(uploaded_or_path, sep=None, engine="python", dtype=str)
    except Exception:
        df = pd.read_csv(uploaded_or_path, dtype=str)
    df = _normalize_headers(df)
    _validate_columns(df)
    for c in REQUIRED_COLUMNS:
        df[c] = df[c].astype(str).fillna("")
    df = df.drop_duplicates(subset=["Stage","Capability"], keep="first").reset_index(drop=True)
    return df

def dataframe_to_items(df: pd.DataFrame):
    return [
        {
            "Stage": r["Stage"], "Capability": r["Capability"],
            "Beginner": r["Beginner"], "Intermediate": r["Intermediate"],
            "Advanced": r["Advanced"], "Expert": r["Expert"],
            "Next-Gen (2025+)": r["Next-Gen (2025+)"],
        } for _, r in df.iterrows()
    ]

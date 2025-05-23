import streamlit as st
from sre_core.init_app import init_app

# Page config
st.set_page_config(page_title="SRE Maturity", layout="wide")

# Init shared state, no sidebar controls
init_app(show_sidebar_controls=False)

# Main welcome text
st.title("SRE Maturity Assessment")
st.markdown("""
Welcome to the **SRE Maturity Assessment Tool**.

Use the sidebar navigation to:
- **Assessment** – Upload capabilities, manage products, and fill in assessments.
- **Visual Report** – View radar charts by stage and capability.
- **Text Report** – View a formatted textual report.
- **PDF Report** – Download a PDF version with charts and findings.
""")

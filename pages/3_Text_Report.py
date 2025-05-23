import streamlit as st
from sre_core.init_app import init_app
from sre_core import formatting

init_app(show_sidebar_controls=False)

st.title("SRE Maturity Text Report")

if st.session_state.cap_df is None:
    st.info("No capabilities loaded. Go to the Assessment page to upload a CSV.")
else:
    report = formatting.markdown_report(
        st.session_state.selected_product,
        st.session_state.maturity_items,
        st.session_state.responses_all.get(st.session_state.selected_product, {}),
    )
    st.markdown(report, unsafe_allow_html=True)

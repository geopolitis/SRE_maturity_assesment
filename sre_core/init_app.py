import io
import streamlit as st
from sre_core import data_io, persistence

DEFAULT_CAP_FILE = "Capabilities.csv"  # local fallback if you want it

def _set_page_config_once():
    if not st.session_state.get("_page_cfg_set"):
        st.set_page_config(page_title="SRE Maturity", layout="wide")
        st.session_state["_page_cfg_set"] = True

def init_app(show_sidebar_controls: bool):
    """
    Initialize shared state for every page.
    If show_sidebar_controls=True, render the CSV uploader and Product Management
    in the sidebar (Assessment page only). Other pages call with False so the
    sidebar stays clean.
    """
    _set_page_config_once()

    # --- core session keys ---
    st.session_state.setdefault("responses_all", persistence.load_responses())
    st.session_state.setdefault("cap_df", None)
    st.session_state.setdefault("uploaded_csv_content", None)
    st.session_state.setdefault("maturity_items", [])
    st.session_state.setdefault("selected_product", None)

    # --------- Assessment page: show controls ----------
    if show_sidebar_controls:
        # Capabilities Data
        st.sidebar.header("Capabilities Data")
        uploaded = st.sidebar.file_uploader("Upload Capabilities CSV", type=["csv"])
        if uploaded:
            # persist raw bytes so other pages can load without re-upload
            st.session_state.uploaded_csv_content = uploaded.getvalue()
            st.session_state.cap_df = data_io.load_capabilities(uploaded)
        else:
            # If nothing uploaded yet but we have bytes from a prior session run, reuse them
            if st.session_state.uploaded_csv_content:
                buf = io.BytesIO(st.session_state.uploaded_csv_content)
                st.session_state.cap_df = data_io.load_capabilities(buf)
            else:
                # Optional local default
                try:
                    st.session_state.cap_df = data_io.load_capabilities(DEFAULT_CAP_FILE)
                    st.sidebar.info(f"Using local {DEFAULT_CAP_FILE}")
                except Exception:
                    st.sidebar.warning("No capabilities loaded yet.")

        # Build maturity items for UI/rendering
        if st.session_state.cap_df is not None:
            st.session_state.maturity_items = data_io.dataframe_to_items(st.session_state.cap_df)
        else:
            st.session_state.maturity_items = []

        # Product Management
        st.sidebar.header("Product Management")
        if not st.session_state.responses_all:
            st.session_state.responses_all = {"Default": {}}
            persistence.save_responses(st.session_state.responses_all)

        new_product = st.sidebar.text_input("Add new product")
        if new_product and new_product not in st.session_state.responses_all:
            st.session_state.responses_all[new_product] = {}
            persistence.save_responses(st.session_state.responses_all)

        # Select product
        product_names = list(st.session_state.responses_all) or ["Default"]
        selected = st.sidebar.selectbox("Select product", product_names)
        st.session_state.selected_product = selected

        if st.sidebar.button("Delete selected product"):
            st.session_state.responses_all.pop(selected, None)
            persistence.save_responses(st.session_state.responses_all)
            st.rerun()

        rename_product = st.sidebar.text_input("Rename selected product")
        if (
            rename_product
            and rename_product != selected
            and rename_product not in st.session_state.responses_all
        ):
            st.session_state.responses_all[rename_product] = st.session_state.responses_all.pop(
                selected
            )
            persistence.save_responses(st.session_state.responses_all)
            st.rerun()

    # --------- Other pages: no sidebar controls ----------
    else:
        # Do NOT render uploader or product mgmt.
        # Just ensure we can reconstruct the capabilities DF if it exists in memory.
        if st.session_state.cap_df is None and st.session_state.uploaded_csv_content:
            buf = io.BytesIO(st.session_state.uploaded_csv_content)
            st.session_state.cap_df = data_io.load_capabilities(buf)

        # If still None, leave it; the page should show a message to visit Assessment to upload.
        if st.session_state.cap_df is not None:
            st.session_state.maturity_items = data_io.dataframe_to_items(st.session_state.cap_df)

        # Ensure a selected product (use first available)
        if st.session_state.selected_product is None:
            if st.session_state.responses_all:
                st.session_state.selected_product = list(st.session_state.responses_all)[0]
            else:
                st.session_state.responses_all = {"Default": {}}
                st.session_state.selected_product = "Default"
                persistence.save_responses(st.session_state.responses_all)

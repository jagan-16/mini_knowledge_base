"""
streamlit_app.py

Entry point. Run with:
    streamlit run streamlit_app.py

This file only orchestrates: init state, do the one-time startup fetch,
render sidebar, render chat. All actual logic lives in the other modules.
"""

import streamlit as st

import api_client
from session_state import init_session_state
from ui_sidebar import render_sidebar
from ui_chat import render_chat_area


st.set_page_config(
    page_title="Mini Knowledge Base",
    page_icon="📚",
    layout="wide",
)

init_session_state()

# One-time startup fetch: documents + conversations, so a page refresh
# doesn't lose anything. The backend is the source of truth.
if not st.session_state.startup_loaded:
    with st.spinner("Loading..."):
        docs_ok, docs = api_client.get_documents()
        if docs_ok:
            st.session_state.documents = docs

        convs_ok, convs = api_client.get_conversations()
        if convs_ok:
            st.session_state.conversations = convs

    st.session_state.startup_loaded = True

render_sidebar()
render_chat_area()

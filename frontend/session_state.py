"""
session_state.py

Single source of truth for what lives in st.session_state, and how it's
initialized. The backend (Postgres) is the real source of truth for
documents and conversation history — session_state here just holds
what's needed to render the current page without refetching everything
on every rerun.
"""

import streamlit as st


def init_session_state():
    """Set every session_state key we rely on, if not already present."""
    defaults = {
        "documents": [],              # list of document dicts from GET /documents
        "conversations": [],          # list of conversation dicts from GET /conversations
        "selected_document_type": None,
        "selected_department": None,
        "current_conversation_id": None,
        "selected_document_id": None,
        "messages": [],               # current conversation's messages, each: {role, content, citations?}
        "startup_loaded": False,  
        "upload_success_message": None,
        "upload_key_suffix": 0,# guards the one-time fetch on first load
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_conversation():
    """Start a fresh conversation — clears current chat, keeps documents/filters."""
    st.session_state.current_conversation_id = None
    st.session_state.messages = []


def set_conversation(conversation_id: str, messages: list):
    """Load an existing conversation's messages into session_state."""
    st.session_state.current_conversation_id = conversation_id
    st.session_state.messages = messages


def append_message(role: str, content: str, citations: list | None = None):
    st.session_state.messages.append(
        {"role": role, "content": content, "citations": citations or []}
    )
def render_search_filters():

    st.sidebar.markdown("### 🔍 Search Filters")

    documents = st.session_state.documents

    if not documents:
        st.sidebar.caption("Upload documents to enable filters.")
        return

    document_types = sorted(

        {
            doc["document_type"]
            for doc in documents
            if doc.get("document_type")
        }

    )

    departments = sorted(

        {
            doc["department"]
            for doc in documents
            if doc.get("department")
        }

    )

    scope = st.sidebar.radio(

        "Search Scope",

        [

            "Entire Knowledge Base",

            "Single Document",

            "Document Type",

            "Department",

        ],

    )

    if scope == "Entire Knowledge Base":

        st.session_state.selected_document_id = None
        st.session_state.selected_document_type = None
        st.session_state.selected_department = None

    elif scope == "Document Type":

        st.session_state.selected_document_id = None
        st.session_state.selected_department = None

        selected = st.sidebar.selectbox(

            "Document Type",

            document_types,

        )

        st.session_state.selected_document_type = selected

    elif scope == "Department":

        st.session_state.selected_document_id = None
        st.session_state.selected_document_type = None

        selected = st.sidebar.selectbox(

            "Department",

            departments,

        )

        st.session_state.selected_department = selected

    elif scope == "Single Document":

        st.session_state.selected_document_type = None
        st.session_state.selected_department = None
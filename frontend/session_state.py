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
        "current_conversation_id": None,
        "selected_document_id": None,
        "messages": [],               # current conversation's messages, each: {role, content, citations?}
        "startup_loaded": False,      # guards the one-time fetch on first load
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

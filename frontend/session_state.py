"""
session_state.py

Single source of truth for what lives in st.session_state, and how it's
initialized. The backend (Postgres) is the real source of truth for
documents and conversation history — session_state here just holds
what's needed to render the current page without refetching everything
on every rerun.

Search is organized into three mutually exclusive, explicitly chosen
scopes: Entire Knowledge Base, Single Document, and Metadata Filters.
Choosing one scope disables the others rather than letting the user
accidentally combine document selection with metadata filters in a way
the backend doesn't support (it treats document_id and metadata_filters
as mutually exclusive). Within "Metadata Filters" scope, any number of
fields can be added simultaneously as an AND-combined filter.
"""

import streamlit as st

SEARCH_SCOPES = ["Entire Knowledge Base", "Single Document", "Metadata Filters"]


def init_session_state():
    """Set every session_state key we rely on, if not already present."""
    defaults = {
        "documents": [],              # list of document dicts from GET /documents
        "conversations": [],          # list of conversation dicts from GET /conversations
        "search_scope": SEARCH_SCOPES[0],
        "selected_metadata_filters": {},  # generic {field: value} dict, built dynamically
        "current_conversation_id": None,
        "selected_document_id": None,
        "messages": [],               # current conversation's messages, each: {role, content, citations?}
        "startup_loaded": False,      # guards the one-time fetch on first load
        "upload_success_message": None,
        "upload_key_suffix": 0,
        "add_filter_key_suffix": 0,   # bumped after each add, to reset the "add filter" widgets
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


def _values_for_field(doc: dict, field: str) -> list:
    """
    Return whatever value(s) a document has for a metadata field, as a
    list, regardless of whether the underlying value is a single string
    or a list of strings. Never raises on unexpected shapes.
    """
    raw = (doc.get("metadata") or {}).get(field)
    if raw is None:
        return []
    if isinstance(raw, list):
        return [v for v in raw if v is not None]
    return [raw]


def _render_metadata_filter_controls():
    """Chip-based add/remove UI for metadata filters, shown only in 'Metadata Filters' scope."""
    documents = st.session_state.documents

    metadata_fields = sorted({
        key
        for doc in documents
        for key in (doc.get("metadata") or {}).keys()
    })

    if not metadata_fields:
        st.sidebar.caption("Uploaded documents have no metadata to filter by.")
        return

    field_labels = {field: field.replace("_", " ").title() for field in metadata_fields}
    active_filters = st.session_state.selected_metadata_filters

    if active_filters:
        for field, value in list(active_filters.items()):
            chip_col, remove_col = st.sidebar.columns([5, 1])
            chip_col.markdown(f"🔹 **{field_labels.get(field, field)}**: {value}")
            if remove_col.button("✕", key=f"remove_filter_{field}"):
                del st.session_state.selected_metadata_filters[field]
                st.rerun()

        if st.sidebar.button("Clear all filters", use_container_width=True):
            st.session_state.selected_metadata_filters = {}
            st.rerun()
    else:
        st.sidebar.caption("No filters added yet.")

    available_fields = [f for f in metadata_fields if f not in active_filters]

    if not available_fields:
        return

    suffix = st.session_state.add_filter_key_suffix

    with st.sidebar.expander("➕ Add filter", expanded=False):
        field_to_add = st.selectbox(
            "Field",
            available_fields,
            format_func=lambda f: field_labels[f],
            key=f"add_filter_field_{suffix}",
        )

        values = sorted({
            value
            for doc in documents
            for value in _values_for_field(doc, field_to_add)
        })

        if not values:
            st.caption(f"No values available for {field_labels[field_to_add]}.")
            return

        value_to_add = st.selectbox("Value", values, key=f"add_filter_value_{suffix}")

        if st.button("Add filter", key=f"add_filter_submit_{suffix}"):
            st.session_state.selected_metadata_filters[field_to_add] = value_to_add
            st.session_state.add_filter_key_suffix += 1
            st.rerun()


def render_search_filters():
    """
    Renders the top-level search scope selector, and whatever controls
    are relevant to the chosen scope. This is the single guided entry
    point for how the user restricts their search:

        Entire Knowledge Base -> no restriction at all
        Single Document       -> restrict to one document, selected in
                                  the Documents section below (only
                                  enabled while this scope is active)
        Metadata Filters      -> restrict by one or more metadata fields
                                  simultaneously (AND-combined)

    Switching scope always clears whatever the other scopes had set, so
    there's never a stale document_id lingering under Metadata Filters
    scope or vice versa.
    """
    st.sidebar.markdown("### 🔍 Search Scope")

    documents = st.session_state.documents
    if not documents:
        st.sidebar.caption("Upload documents to enable search scoping.")
        return

    scope = st.sidebar.radio("Choose how to search", SEARCH_SCOPES, key="search_scope")

    if scope == "Entire Knowledge Base":
        st.session_state.selected_document_id = None
        st.session_state.selected_metadata_filters = {}
        st.sidebar.caption("Searching the entire knowledge base.")

    elif scope == "Single Document":
        st.session_state.selected_metadata_filters = {}
        st.sidebar.caption(
            "Select a document under 'Documents' below to search only that document."
        )
        # Actual document selection happens in ui_sidebar.render_documents_section(),
        # which checks st.session_state.search_scope before enabling its button.

    elif scope == "Metadata Filters":
        st.session_state.selected_document_id = None
        _render_metadata_filter_controls()
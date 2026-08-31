"""
session_state.py

Single source of truth for what lives in st.session_state, and how it's
initialized. The backend (Postgres) is the real source of truth for
documents and conversation history — session_state here just holds
what's needed to render the current page without refetching everything
on every rerun.

Metadata filtering uses an explicit "add filter" pattern rather than
always-visible per-field dropdowns. Only filters the user has actually
added appear at all, each as a removable chip — there's no ambiguous
"All" dropdown sitting there that might be mistaken for an active
constraint. Field discovery itself remains fully dynamic: nothing is
hardcoded to specific field names like "department" or "language".
"""

import streamlit as st


def init_session_state():
    """Set every session_state key we rely on, if not already present."""
    defaults = {
        "documents": [],              # list of document dicts from GET /documents
        "conversations": [],          # list of conversation dicts from GET /conversations
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
    or a list of strings (a document tagged with multiple departments,
    for example). Never raises on unexpected shapes.
    """
    raw = (doc.get("metadata") or {}).get(field)
    if raw is None:
        return []
    if isinstance(raw, list):
        return [v for v in raw if v is not None]
    return [raw]


def render_search_filters():
    """
    Renders active metadata filters as removable chips, plus an
    "+ Add filter" control to add more. Nothing is ever shown as filtered
    unless the user explicitly added it — there is no default-"All"
    dropdown that could be mistaken for an active constraint.

    Semantics (unchanged from before, just the UI changed):
      - No chips  -> search the entire knowledge base.
      - One chip  -> filter by that single field.
      - Multiple chips -> AND all of them together.

    Metadata filtering and single-document selection remain mutually
    exclusive on the backend, so this section disables itself whenever a
    specific document is currently selected.
    """
    st.sidebar.markdown("### 🔍 Search Filters")

    if st.session_state.selected_document_id:
        st.sidebar.caption(
            "A single document is selected below — metadata filters are "
            "disabled while a specific document is active. Clear the "
            "document selection to filter by metadata instead."
        )
        st.session_state.selected_metadata_filters = {}
        return

    documents = st.session_state.documents

    if not documents:
        st.sidebar.caption("Upload documents to enable filters.")
        return

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

    # ------------------------------------------------------------
    # Active filters, shown only if they exist -- as removable chips
    # ------------------------------------------------------------
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
        st.sidebar.caption("No filters applied — searching the entire knowledge base.")

    # ------------------------------------------------------------
    # Add a new filter -- only fields not already filtered are offered
    # ------------------------------------------------------------
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
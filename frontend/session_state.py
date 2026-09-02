"""
session_state.py

Single source of truth for what lives in st.session_state, and how it's
initialized. The backend (Postgres) is the real source of truth for
documents and conversation history — session_state here just holds
what's needed to render the current page without refetching everything
on every rerun.

Metadata filtering now targets the backend's operator-based filter tree
(eq / neq / in / not_in, combined with and/or). This UI builds one
condition per field the user adds, each with its own chosen operator,
plus a single global group operator (and/or) that combines every active
condition together — so cross-field OR is possible (e.g. department =
Engineering OR document_type = Policy). What this UI still does NOT
expose is mixed nesting (e.g. A AND (B OR C)): every active condition
is combined at one flat level, all-AND or all-OR, never both in the
same query. The backend's tree format supports arbitrary nesting; this
UI intentionally exposes only the flat subset, to keep the sidebar
simple.
"""

import streamlit as st

SEARCH_SCOPES = ["Entire Knowledge Base", "Single Document", "Metadata Filters"]

# Maps the operator sent to the backend -> human-readable label shown in the UI
OPERATOR_LABELS = {
    "eq": "is",
    "neq": "is not",
    "in": "is any of",
    "not_in": "is none of",
}
MULTI_VALUE_OPERATORS = {"in", "not_in"}


def init_session_state():
    """Set every session_state key we rely on, if not already present."""
    defaults = {
        "documents": [],              # list of document dicts from GET /documents
        "conversations": [],          # list of conversation dicts from GET /conversations
        "search_scope": SEARCH_SCOPES[0],
        # keyed by field name -> {"operator": "eq"|"neq"|"in"|"not_in", "value": str | list[str]}
        "selected_metadata_conditions": {},
        # "and" | "or" — how selected_metadata_conditions combine at the top level
        "metadata_group_operator": "and",
        "current_conversation_id": None,
        "selected_document_id": None,
        "messages": [],               # current conversation's messages, each: {role, content, citations?}
        "startup_loaded": False,      # guards the one-time fetch on first load
        "upload_success_message": None,
        "upload_key_suffix": 0,
        "add_filter_key_suffix": 0,   # bumped after each add, to reset the "add filter" widgets
        # Set by "Clear all filters" to request a reset that must happen
        # BEFORE the metadata_group_operator radio widget renders next
        # run — see _render_metadata_filter_controls for why.
        "_reset_metadata_filters": False,
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


def build_metadata_filter_payload() -> dict | None:
    """
    Turn the active per-field conditions into the backend's operator-tree
    shape, combined at the top level by the user's chosen group operator
    (and/or):

        {
            "operator": "or",
            "conditions": [
                {"field": "department", "operator": "eq", "value": "Engineering"},
                {"field": "document_type", "operator": "in", "value": ["Policy", "Technical Documentation"]}
            ]
        }

    This is always a single flat group — every active condition combined
    with one operator, never a mix of and/or in the same request. That's
    a deliberate UI scope limit, not a backend limit; the backend tree
    format supports arbitrary nesting.

    Returns None if there are no active conditions, so callers can omit
    metadata_filters from the request entirely (matching how api_client
    already treats a falsy metadata_filters value).
    """
    conditions = st.session_state.selected_metadata_conditions

    if not conditions:
        return None

    return {
        "operator": st.session_state.get("metadata_group_operator", "and"),
        "conditions": [
            {"field": field, "operator": cond["operator"], "value": cond["value"]}
            for field, cond in conditions.items()
        ],
    }


def _describe_condition(field_label: str, operator: str, value) -> str:
    op_label = OPERATOR_LABELS[operator]
    value_str = ", ".join(value) if isinstance(value, list) else value
    return f"{field_label} {op_label}: {value_str}"


def _render_metadata_filter_controls():
    """Chip-based add/remove UI for operator-based metadata filters."""

    # Apply any reset requested by "Clear all filters" on a previous run,
    # BEFORE the metadata_group_operator radio widget below gets
    # instantiated this run. Streamlit forbids writing to a widget-keyed
    # session_state entry in the same run after that widget has already
    # rendered — so the reset can't happen inside the button's own click
    # handler (which runs after the radio, later in this same function).
    # Deferring it to the top of the *next* run, before the radio exists
    # yet, is the standard workaround.
    if st.session_state._reset_metadata_filters:
        st.session_state.selected_metadata_conditions = {}
        st.session_state.metadata_group_operator = "and"
        st.session_state._reset_metadata_filters = False

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
    active_conditions = st.session_state.selected_metadata_conditions

    # ------------------------------------------------------------
    # Group operator — only meaningful with 2+ active conditions.
    # Governs how ALL active conditions combine (flat, not nested):
    # every condition ANDed together, or every condition ORed together.
    # ------------------------------------------------------------
    if len(active_conditions) >= 2:
        st.sidebar.radio(
            "Combine filters using",
            ["and", "or"],
            format_func=lambda op: "Match ALL filters (AND)" if op == "and" else "Match ANY filter (OR)",
            key="metadata_group_operator",
            horizontal=True,
        )
        st.sidebar.caption(
            "Applies to every filter below together — mixing AND and OR "
            "in one query isn't supported yet."
        )

    # ------------------------------------------------------------
    # Active filters, shown as removable chips with their operator
    # ------------------------------------------------------------
    if active_conditions:
        for field, cond in list(active_conditions.items()):
            chip_col, remove_col = st.sidebar.columns([5, 1])
            description = _describe_condition(field_labels.get(field, field), cond["operator"], cond["value"])
            chip_col.markdown(f"🔹 **{description}**")
            if remove_col.button("✕", key=f"remove_filter_{field}"):
                del st.session_state.selected_metadata_conditions[field]
                st.rerun()

        if st.sidebar.button("Clear all filters", use_container_width=True):
            st.session_state._reset_metadata_filters = True
            st.rerun()
    else:
        st.sidebar.caption("No filters added yet.")

    available_fields = [f for f in metadata_fields if f not in active_conditions]

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

        possible_values = sorted({
            value
            for doc in documents
            for value in _values_for_field(doc, field_to_add)
        })

        if not possible_values:
            st.caption(f"No values available for {field_labels[field_to_add]}.")
            return

        operator = st.selectbox(
            "Condition",
            list(OPERATOR_LABELS.keys()),
            format_func=lambda op: OPERATOR_LABELS[op],
            key=f"add_filter_operator_{suffix}",
        )

        # Widget key includes the operator so switching between a
        # single-value operator (eq/neq) and a multi-value operator
        # (in/not_in) always gets a fresh widget of the right type,
        # rather than reusing stale state from a different widget kind.
        if operator in MULTI_VALUE_OPERATORS:
            value_to_add = st.multiselect(
                "Values", possible_values, key=f"add_filter_value_{operator}_{suffix}"
            )
            can_add = len(value_to_add) > 0
        else:
            value_to_add = st.selectbox(
                "Value", possible_values, key=f"add_filter_value_{operator}_{suffix}"
            )
            can_add = True

        if st.button("Add filter", key=f"add_filter_submit_{suffix}", disabled=not can_add):
            st.session_state.selected_metadata_conditions[field_to_add] = {
                "operator": operator,
                "value": value_to_add,
            }
            st.session_state.add_filter_key_suffix += 1
            st.rerun()


def render_search_filters():
    """
    Renders the top-level search scope selector, and whatever controls
    are relevant to the chosen scope.

        Entire Knowledge Base -> no restriction at all
        Single Document       -> restrict to one document, selected in
                                  the Documents section below (only
                                  enabled while this scope is active)
        Metadata Filters      -> one or more field conditions, each with
                                  its own operator (is / is not / is any
                                  of / is none of), combined at the top
                                  level by a single AND/OR group toggle
    """
    st.sidebar.markdown("### 🔍 Search Scope")

    documents = st.session_state.documents
    if not documents:
        st.sidebar.caption("Upload documents to enable search scoping.")
        return

    scope = st.sidebar.radio("Choose how to search", SEARCH_SCOPES, key="search_scope")

    if scope == "Entire Knowledge Base":
        st.session_state.selected_document_id = None
        st.session_state.selected_metadata_conditions = {}
        st.session_state.metadata_group_operator = "and"
        st.sidebar.caption("Searching the entire knowledge base.")

    elif scope == "Single Document":
        st.session_state.selected_metadata_conditions = {}
        st.session_state.metadata_group_operator = "and"
        st.sidebar.caption(
            "Select a document under 'Documents' below to search only that document."
        )

    elif scope == "Metadata Filters":
        st.session_state.selected_document_id = None
        _render_metadata_filter_controls()
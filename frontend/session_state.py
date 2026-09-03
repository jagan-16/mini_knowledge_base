"""
session_state.py

Single source of truth for Streamlit session state, including the
metadata filter builder used by the backend query API.

The metadata filter UI is a flat, linear list of condition rows. Each
row after the first carries a connector ("and"/"or") chosen at the time
it was added, describing how it combines with everything above it.
Standard AND-before-OR precedence turns that flat list into the
backend's nested operator tree before it's sent:

    A AND B OR C AND D  ->  (A AND B) OR (C AND D)

SCOPE LIMIT, stated plainly: fixed precedence can express "OR of
AND-groups" (sum of products) but NOT "AND of OR-groups" — e.g.
`A AND (B OR C)` has no representation here, because AND always binds
tighter than OR under precedence parsing, with no explicit grouping
syntax to override that locally. If that shape is needed, this UI
can't produce it.

Connectors are chosen once, when a row is added, and are not editable
afterwards — only removable (delete the row, re-add with a different
connector). This avoids Streamlit's "cannot modify a widget-keyed
session_state entry after that widget has already rendered this run"
class of bug, which this file has already hit twice with earlier,
more editable designs.

Example resulting payload for `A AND B OR C AND D`:
{
    "operator": "or",
    "conditions": [
        {"operator": "and", "conditions": [{"field": "A", ...}, {"field": "B", ...}]},
        {"operator": "and", "conditions": [{"field": "C", ...}, {"field": "D", ...}]}
    ]
}
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import streamlit as st

SEARCH_SCOPES = ["Entire Knowledge Base", "Single Document", "Metadata Filters"]

# Maps the operator sent to the backend -> human-readable label shown in the UI
OPERATOR_LABELS = {
    "eq": "is",
    "neq": "is not",
    "in": "is any of",
    "not_in": "is none of",
    "gte": ">=",
    "lte": "<=",
    "gt": ">",
    "lt": "<",
}
MULTI_VALUE_OPERATORS = {"in", "not_in"}


def init_session_state():
    """Set every session_state key we rely on, if not already present."""
    defaults = {
        "documents": [],              # list of document dicts from GET /documents
        "conversations": [],          # list of conversation dicts from GET /conversations
        "search_scope": SEARCH_SCOPES[0],
        # Flat list of condition rows:
        #   {"id": str, "connector": "and"|"or"|None, "field": str, "operator": str, "value": str|list[str]}
        # row[0]["connector"] is always None (nothing precedes it).
        "metadata_filter_rows": [],
        "current_conversation_id": None,
        "selected_document_id": None,
        "messages": [],               # current conversation's messages, each: {role, content, citations?}
        "startup_loaded": False,      # guards the one-time fetch on first load
        "upload_success_message": None,
        "upload_key_suffix": 0,
        "metadata_condition_key_suffix": 0,   # bumped after each add, to reset the "add condition" widgets
        # Set by "Clear all filters" to request a reset that must happen
        # BEFORE the "add condition" widgets render next run — see
        # _render_metadata_filter_controls for why.
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


def _build_tree_from_rows(rows: list[dict]) -> dict | None:
    """
    Pure function: flat rows (with per-row connector) -> nested operator
    tree, via AND-before-OR precedence. No Streamlit dependency, so this
    is directly unit-testable.

    Returns:
      - None if rows is empty
      - a bare {"field","operator","value"} dict if there's exactly one row
      - a {"operator","conditions":[...]} group otherwise
    """
    if not rows:
        return None

    conditions = [
        {"field": r["field"], "operator": r["operator"], "value": r["value"]}
        for r in rows
    ]

    if len(conditions) == 1:
        return conditions[0]

    connectors = [r["connector"] for r in rows[1:]]  # connector before rows[1], rows[2], ...

    if "or" not in connectors:
        return {"operator": "and", "conditions": conditions}

    # Split into maximal AND-runs at each OR boundary.
    runs = []
    current_run = [conditions[0]]
    for cond, conn in zip(conditions[1:], connectors):
        if conn == "or":
            runs.append(current_run)
            current_run = [cond]
        else:
            current_run.append(cond)
    runs.append(current_run)

    group_nodes = [
        run[0] if len(run) == 1 else {"operator": "and", "conditions": run}
        for run in runs
    ]

    if len(group_nodes) == 1:
        return group_nodes[0]

    return {"operator": "or", "conditions": group_nodes}


def build_metadata_filter_payload() -> dict | None:
    """
    Compile the flat row list into the backend's operator-tree shape.
    Returns None if there are no rows, so callers can omit
    metadata_filters from the request entirely (matching how api_client
    already treats a falsy metadata_filters value).
    """
    rows = st.session_state.metadata_filter_rows
    tree = _build_tree_from_rows(rows)

    if tree is None:
        return None

    # A single bare condition still needs the top-level {"operator","conditions"}
    # shape the backend expects.
    if "conditions" not in tree:
        return {"operator": "and", "conditions": [tree]}

    return tree


def _describe_condition(field_label: str, operator: str, value: Any) -> str:
    op_label = OPERATOR_LABELS[operator]
    value_str = ", ".join(map(str, value)) if isinstance(value, list) else str(value)
    return f"{field_label} {op_label}: {value_str}"


def _reset_filter_state():
    st.session_state.metadata_filter_rows = []


def _render_metadata_filter_controls():
    """Flat, linear rule-builder for operator-based metadata filters."""

    # Apply any reset requested by "Clear all filters" on a previous
    # run, before the "add condition" widgets below render this run —
    # same deferred-reset pattern used elsewhere in this file, for the
    # same Streamlit widget-key reason.
    if st.session_state._reset_metadata_filters:
        _reset_filter_state()
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
    rows = st.session_state.metadata_filter_rows

    # ------------------------------------------------------------
    # Saved rows, shown as a plain vertical list with the connector
    # printed between consecutive rows. Not editable in place — only
    # removable — see module docstring for why.
    # ------------------------------------------------------------
    if rows:
        for index, row in enumerate(list(rows)):
            if index > 0:
                connector_label = "AND" if row["connector"] == "and" else "OR"
                st.sidebar.caption(f"— {connector_label} —")

            chip_col, remove_col = st.sidebar.columns([5, 1])
            description = _describe_condition(
                field_labels.get(row["field"], row["field"]), row["operator"], row["value"]
            )
            chip_col.markdown(f"🔹 **{description}**")
            if remove_col.button("✕", key=f"remove_row_{row['id']}"):
                rows.remove(row)
                st.rerun()

        if st.sidebar.button("Clear all filters", use_container_width=True):
            st.session_state._reset_metadata_filters = True
            st.rerun()
    else:
        st.sidebar.caption("No filters added yet.")

    # ------------------------------------------------------------
    # Add condition
    # ------------------------------------------------------------
    suffix = st.session_state.metadata_condition_key_suffix

    with st.sidebar.expander("➕ Add condition", expanded=not rows):
        connector = None
        if rows:
            connector = st.selectbox(
                "Combine with the filters above using",
                ["and", "or"],
                format_func=lambda op: "AND" if op == "and" else "OR",
                key=f"add_row_connector_{suffix}",
            )

        field_to_add = st.selectbox(
            "Field",
            metadata_fields,
            format_func=lambda f: field_labels[f],
            key=f"add_row_field_{suffix}",
        )

        def _value_sort_key(value):
            # Numeric-looking values sort numerically (matters for the
            # comparison operators), everything else falls back to
            # plain string sort.
            try:
                return (0, float(value))
            except (TypeError, ValueError):
                return (1, str(value))

        possible_values = sorted(
            {
                value
                for doc in documents
                for value in _values_for_field(doc, field_to_add)
                if value is not None
            },
            key=_value_sort_key,
        )

        operator = st.selectbox(
            "Condition",
            list(OPERATOR_LABELS.keys()),
            format_func=lambda op: OPERATOR_LABELS[op],
            key=f"add_row_operator_{suffix}",
        )

        if not possible_values:
            st.caption(f"No values available for {field_labels[field_to_add]}.")
            return

        # Widget key includes the operator so switching between a
        # single-value operator and a multi-value operator (in/not_in)
        # always gets a fresh widget of the right type.
        if operator in MULTI_VALUE_OPERATORS:
            value_to_add = st.multiselect(
                "Values", possible_values, key=f"add_row_value_{operator}_{suffix}"
            )
            can_add = len(value_to_add) > 0
        else:
            value_to_add = st.selectbox(
                "Value", possible_values, key=f"add_row_value_{operator}_{suffix}"
            )
            can_add = True

        if st.button(
            "Add condition", key=f"add_row_submit_{suffix}", disabled=not can_add, use_container_width=True
        ):
            rows.append({
                "id": uuid4().hex,
                "connector": connector,
                "field": field_to_add,
                "operator": operator,
                "value": value_to_add,
            })
            st.session_state.metadata_condition_key_suffix += 1
            st.rerun()


def render_search_filters():
    """
    Renders the top-level search scope selector, and whatever controls
    are relevant to the chosen scope.

        Entire Knowledge Base -> no restriction at all
        Single Document       -> restrict to one document, selected in
                                  the Documents section below (only
                                  enabled while this scope is active)
        Metadata Filters      -> a flat, ordered list of conditions,
                                  each combined with everything above it
                                  via a connector chosen when it was
                                  added (AND-before-OR precedence)
    """
    st.sidebar.markdown("### 🔍 Search Scope")

    documents = st.session_state.documents
    if not documents:
        st.sidebar.caption("Upload documents to enable search scoping.")
        return

    scope = st.sidebar.radio("Choose how to search", SEARCH_SCOPES, key="search_scope")

    # These two branches are mutually exclusive with the one that calls
    # _render_metadata_filter_controls() below, so none of that
    # function's widgets are instantiated in the same run here — direct
    # assignment is safe in this branch, no deferred-reset flag needed.
    if scope == "Entire Knowledge Base":
        st.session_state.selected_document_id = None
        _reset_filter_state()
        st.sidebar.caption("Searching the entire knowledge base.")

    elif scope == "Single Document":
        _reset_filter_state()
        st.sidebar.caption(
            "Select a document under 'Documents' below to search only that document."
        )

    elif scope == "Metadata Filters":
        st.session_state.selected_document_id = None
        _render_metadata_filter_controls()
"""
session_state.py

Single source of truth for Streamlit session state, including the two-level
metadata filter builder used by the backend query API.

The metadata filter UI intentionally supports two levels of nesting:

    outer operator
        group 1: inner operator + conditions
        group 2: inner operator + conditions
        ...

Example payload:
{
    "operator": "or",
    "conditions": [
        {
            "operator": "and",
            "conditions": [
                {"field": "department", "operator": "eq", "value": "Engineering"},
                {"field": "document_type", "operator": "eq", "value": "Policy"}
            ]
        },
        {
            "operator": "and",
            "conditions": [
                {"field": "department", "operator": "eq", "value": "HR"},
                {"field": "document_type", "operator": "eq", "value": "Resume"}
            ]
        }
    ]
}

This is deliberately capped at two levels. Arbitrary recursive nesting is not
exposed by the sidebar because it adds a lot of UI complexity without being
necessary for the intended filter use cases.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

import streamlit as st

SEARCH_SCOPES = ["Entire Knowledge Base", "Single Document", "Metadata Filters"]

OPERATOR_LABELS = {
    "eq": "is",
    "neq": "is not",
    "in": "is any of",
    "not_in": "is none of",
    "lt": "< (less than)",
    "gt": "> (greater than)",
    "lte": "<= (less than or equal)",
    "gte": ">= (greater than or equal)",
}

MULTI_VALUE_OPERATORS = {"in", "not_in"}
COMPARISON_OPERATORS = {"lt", "gt", "lte", "gte"}


def init_session_state():
    """Set every session_state key we rely on, if not already present."""
    defaults = {
        "documents": [],
        "conversations": [],
        "search_scope": SEARCH_SCOPES[0],
        # List of groups. Each group has a stable UI id plus:
        # {"id": str, "operator": "and"|"or", "conditions": [condition, ...]}
        "metadata_filter_groups": [],
        # "and" | "or" — combines the active groups.
        "metadata_group_operator": "and",
        "current_conversation_id": None,
        "selected_document_id": None,
        "messages": [],
        "startup_loaded": False,
        "upload_success_message": None,
        "upload_key_suffix": 0,
        "metadata_group_key_suffix": 0,
        "metadata_condition_key_suffix": 0,
        "_reset_metadata_filters": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)

    # Migrate the previous flat representation if the app is upgraded while
    # a user's existing Streamlit session is still alive.
    if "selected_metadata_conditions" in st.session_state and not st.session_state.metadata_filter_groups:
        legacy = st.session_state.get("selected_metadata_conditions") or {}
        if legacy:
            st.session_state.metadata_filter_groups = [
                {
                    "id": uuid4().hex,
                    "operator": st.session_state.get("metadata_group_operator", "and"),
                    "conditions": [
                        {
                            "field": field,
                            "operator": condition["operator"],
                            "value": condition["value"],
                        }
                        for field, condition in legacy.items()
                    ],
                }
            ]
        st.session_state.pop("selected_metadata_conditions", None)


def reset_conversation():
    """Start a fresh conversation while keeping documents and filters."""
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
    """Return a document metadata value as a normalized list."""
    raw = (doc.get("metadata") or {}).get(field)
    if raw is None:
        return []
    if isinstance(raw, list):
        return [v for v in raw if v is not None]
    return [raw]


def build_metadata_filter_payload() -> dict | None:
    """Compile the UI state into the backend's two-level operator tree."""
    groups = st.session_state.get("metadata_filter_groups", [])
    active_groups = [
        {
            "operator": group.get("operator", "and"),
            "conditions": [
                {
                    "field": condition["field"],
                    "operator": condition["operator"],
                    "value": condition["value"],
                }
                for condition in group.get("conditions", [])
                if condition.get("field") and condition.get("operator") and "value" in condition
            ],
        }
        for group in groups
    ]
    active_groups = [group for group in active_groups if group["conditions"]]

    if not active_groups:
        return None

    # A single populated group does not need an outer wrapper. Keeping the
    # group itself as the root also avoids unnecessary nesting for simple use.
    if len(active_groups) == 1:
        return active_groups[0]

    return {
        "operator": st.session_state.get("metadata_group_operator", "and"),
        "conditions": active_groups,
    }


def _describe_condition(field_label: str, operator: str, value: Any) -> str:
    op_label = OPERATOR_LABELS[operator]
    value_str = ", ".join(map(str, value)) if isinstance(value, list) else str(value)
    return f"{field_label} {op_label}: {value_str}"


def _new_group() -> dict:
    return {"id": uuid4().hex, "operator": "and", "conditions": []}


def _group_has_field(group: dict, field: str) -> bool:
    return any(condition.get("field") == field for condition in group.get("conditions", []))


def _render_condition(group_index: int, condition_index: int, field_labels: dict[str, str]):
    """Render a saved condition and the control to remove it."""
    groups = st.session_state.metadata_filter_groups
    condition = groups[group_index]["conditions"][condition_index]
    field = condition["field"]
    description = _describe_condition(
        field_labels.get(field, field), condition["operator"], condition["value"]
    )

    chip_col, remove_col = st.sidebar.columns([6, 1])
    chip_col.caption(f"{description}")
    if remove_col.button(
        "✕",
        key=f"remove_condition_{group_index}_{condition_index}",
        help="Remove this condition",
    ):
        del groups[group_index]["conditions"][condition_index]
        st.rerun()


def _render_add_condition(group_index: int, documents: list[dict], metadata_fields: list[str], field_labels: dict[str, str]):
    """Render controls for adding one condition to a specific group."""
    group = st.session_state.metadata_filter_groups[group_index]
    available_fields = [field for field in metadata_fields if not _group_has_field(group, field)]
    if not available_fields:
        st.caption("All available metadata fields are already used in this group.")
        return

    suffix = st.session_state.metadata_condition_key_suffix
    with st.expander("➕ Add condition", expanded=not group["conditions"]):
        field_to_add = st.selectbox(
            "Field",
            available_fields,
            format_func=lambda field: field_labels[field],
            key=f"add_condition_field_{group_index}_{suffix}",
        )

        possible_values = sorted(
            {
                value
                for doc in documents
                for value in _values_for_field(doc, field_to_add)
                if value is not None
            },
            key=lambda value: str(value),
        )

        operator = st.selectbox(
            "Condition",
            list(OPERATOR_LABELS.keys()),
            format_func=lambda op: OPERATOR_LABELS[op],
            key=f"add_condition_operator_{group_index}_{suffix}",
        )

        if not possible_values:
            st.warning(f"No values are available for {field_labels[field_to_add]}.")
            return

        if operator in MULTI_VALUE_OPERATORS:
            value_to_add = st.multiselect(
                "Values",
                possible_values,
                format_func=str,
                key=f"add_condition_value_multi_{group_index}_{suffix}",
            )
            can_add = bool(value_to_add)
        else:
            # All single-value operators, including <, >, <= and >=, use
            # metadata values fetched from the database. No free-text
            # threshold is accepted by the frontend.
            value_to_add = st.selectbox(
                "Value",
                possible_values,
                format_func=str,
                key=f"add_condition_value_single_{operator}_{group_index}_{suffix}",
            )
            can_add = True

        if st.button(
            "Add condition",
            key=f"add_condition_submit_{group_index}_{suffix}",
            disabled=not can_add,
            use_container_width=True,
        ):
            group["conditions"].append(
                {
                    "field": field_to_add,
                    "operator": operator,
                    "value": value_to_add,
                }
            )
            st.session_state.metadata_condition_key_suffix += 1
            st.rerun()


def _reset_filter_state():
    st.session_state.metadata_filter_groups = []
    st.session_state.metadata_group_operator = "and"
    st.session_state.metadata_group_key_suffix = 0
    st.session_state.metadata_condition_key_suffix = 0


def _render_metadata_filter_controls():
    """Render the two-level metadata filter builder."""
    if st.session_state._reset_metadata_filters:
        _reset_filter_state()
        st.session_state._reset_metadata_filters = False

    documents = st.session_state.documents
    metadata_fields = sorted(
        {
            key
            for doc in documents
            for key in (doc.get("metadata") or {}).keys()
        }
    )

    if not metadata_fields:
        st.sidebar.caption("Uploaded documents have no metadata to filter by.")
        return

    field_labels = {field: field.replace("_", " ").title() for field in metadata_fields}
    groups = st.session_state.metadata_filter_groups
    active_groups = [group for group in groups if group.get("conditions")]

    if len(active_groups) >= 2:
        st.sidebar.radio(
            "Combine groups using",
            ["and", "or"],
            format_func=lambda op: "All groups must match (AND)" if op == "and" else "Any group may match (OR)",
            key="metadata_group_operator",
            horizontal=True,
        )
        st.sidebar.caption("This operator combines the groups. Each group has its own AND/OR operator.")

    if groups:
        for index, group in enumerate(list(groups)):
            group_id = group.setdefault("id", uuid4().hex)
            with st.sidebar.container(border=True):
                header_col, remove_col = st.columns([5, 1])
                header_col.markdown(f"**Group {index + 1}**")
                if remove_col.button("🗑️", key=f"remove_group_{index}", help="Remove this group"):
                    del groups[index]
                    st.rerun()

                # The per-group operator is meaningful once the group has 2+ conditions.
                if len(group["conditions"]) >= 2:
                    st.radio(
                        "Combine conditions",
                        ["and", "or"],
                        format_func=lambda op: "Match ALL (AND)" if op == "and" else "Match ANY (OR)",
                        key=f"metadata_group_operator_{group_id}",
                        horizontal=True,
                    )
                    group["operator"] = st.session_state[f"metadata_group_operator_{group_id}"]

                for condition_index in range(len(group["conditions"])):
                    _render_condition(index, condition_index, field_labels)

                _render_add_condition(index, documents, metadata_fields, field_labels)

        if st.sidebar.button("Clear all filters", use_container_width=True):
            st.session_state._reset_metadata_filters = True
            st.rerun()
    else:
        st.sidebar.caption("No filter groups added yet.")

    if st.sidebar.button("➕ Add group", use_container_width=True):
        groups.append(_new_group())
        st.session_state.metadata_group_key_suffix += 1
        st.rerun()


def render_search_filters():
    """Render search scope and metadata filter controls."""
    st.sidebar.markdown("### 🔍 Search Scope")

    documents = st.session_state.documents
    if not documents:
        st.sidebar.caption("Upload documents to enable search scoping.")
        return

    scope = st.sidebar.radio("Choose how to search", SEARCH_SCOPES, key="search_scope")

    if scope == "Entire Knowledge Base":
        st.session_state.selected_document_id = None
        _reset_filter_state()
        st.sidebar.caption("Searching the entire knowledge base.")

    elif scope == "Single Document":
        _reset_filter_state()
        st.sidebar.caption("Select a document under 'Documents' below to search only that document.")

    else:
        st.session_state.selected_document_id = None
        _render_metadata_filter_controls()

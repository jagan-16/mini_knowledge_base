"""
ui_sidebar.py

Renders the three sidebar sections: Upload, Documents, Conversations.
Each section is a plain function so streamlit_app.py stays readable.
"""

import streamlit as st

import api_client
from config import DOCUMENT_TYPES
from session_state import render_search_filters, reset_conversation, set_conversation
from utils import format_timestamp, conversation_label


def render_upload_section():
    with st.sidebar.expander("📤 Upload Document", expanded=False):

        if st.session_state.upload_success_message:
            st.success(st.session_state.upload_success_message)
            st.session_state.upload_success_message = None

        suffix = st.session_state.upload_key_suffix

        uploaded_file = st.file_uploader(
            "Choose a PDF or TXT file", type=["pdf", "txt"], key=f"upload_file_input_{suffix}"
        )
        document_type = st.selectbox(
            "Document type", DOCUMENT_TYPES, key=f"upload_doc_type_{suffix}"
        )
        department = st.text_input(
            "Department (optional)", key=f"upload_department_{suffix}"
        )

        if st.button("Upload", type="primary", use_container_width=True):
            if uploaded_file is None:
                st.warning("Please choose a file first.")
                return

            with st.spinner("Uploading and processing document..."):
                ok, result = api_client.upload_document(
                    uploaded_file, document_type, department or None
                )

            if ok:
                st.session_state.upload_success_message = (
                    f"Uploaded '{result.get('title', uploaded_file.name)}' successfully."
                )
                st.session_state.upload_key_suffix += 1

                docs_ok, docs = api_client.get_documents()
                if docs_ok:
                    st.session_state.documents = docs
                st.rerun()
            else:
                st.error(f"Upload failed: {result}")
        uploaded_file = st.file_uploader(
            "Choose a PDF or TXT file", type=["pdf", "txt"], key="upload_file_input"
        )
        document_type = st.selectbox("Document type", DOCUMENT_TYPES, key="upload_doc_type")
        department = st.text_input("Department (optional)", key="upload_department")
        if st.button("Upload", type="primary", use_container_width=True, key=f"upload_submit_{suffix}"):
            if uploaded_file is None:
                st.warning("Please choose a file first.")
                return

            with st.spinner("Uploading and processing document..."):
                ok, result = api_client.upload_document(
                    uploaded_file, document_type, department or None
                )

            if ok:
                st.session_state.upload_success_message = f"Uploaded '{result.get('title', uploaded_file.name)}' successfully."
                # Refresh the document list so the new upload shows up immediately
                docs_ok, docs = api_client.get_documents()
                if docs_ok:
                    st.session_state.documents = docs
                st.rerun()
            else:
                st.error(f"Upload failed: {result}")


def render_documents_section():
    st.sidebar.markdown("### 📄 Documents")

    documents = st.session_state.documents

    if not documents:
        st.sidebar.caption("No documents uploaded yet.")
        return

    if st.session_state.selected_document_type is not None:
        st.sidebar.info(
            f"Filtering by document type: {st.session_state.selected_document_type}"
        )

    if st.session_state.selected_department is not None:
        st.sidebar.info(
            f"Filtering by department: {st.session_state.selected_department}"
        )
        
    if st.session_state.selected_document_id:
        if st.sidebar.button("✕ Clear document selection", use_container_width=True):
            st.session_state.selected_document_id = None
            st.rerun()

    for doc in documents:
        doc_id = doc.get("document_id")
        is_selected = doc_id == st.session_state.selected_document_id
        label = f"{'✅ ' if is_selected else ''}{doc.get('title', 'Untitled')}"

        with st.sidebar.container(border=True):
            st.markdown(f"**{label}**")
            meta_bits = []
            if doc.get("document_type"):
                meta_bits.append(doc["document_type"])
            if doc.get("department"):
                meta_bits.append(doc["department"])
            if meta_bits:
                st.caption(" · ".join(meta_bits))
            if doc.get("created_at"):
                st.caption(format_timestamp(doc["created_at"]))

            if st.button(
                "Query only this document" if not is_selected else "Selected",
                key=f"select_doc_{doc_id}",
                disabled=is_selected,
                use_container_width=True,
            ):
                st.session_state.selected_document_id = doc_id
                st.rerun()


def render_conversations_section():
    st.sidebar.markdown("### 💬 Conversations")

    if st.sidebar.button("➕ New conversation", use_container_width=True):
        reset_conversation()
        st.rerun()

    conversations = st.session_state.conversations
    if not conversations:
        st.sidebar.caption("No conversations yet.")
        return

    # Number conversations by creation order (oldest = 1), then display newest first
    sorted_by_created = sorted(conversations, key=lambda c: c.get("created_at", ""))
    numbered = [
        (index + 1, conv) for index, conv in enumerate(sorted_by_created)
    ]
    newest_first = list(reversed(numbered))

    for number, conv in newest_first:
        conv_id = conv.get("conversation_id")
        is_current = conv_id == st.session_state.current_conversation_id
        label = f"{'▶ ' if is_current else ''}{conversation_label(number)}"

        if st.sidebar.button(label, key=f"conv_{conv_id}", use_container_width=True):
            with st.spinner("Loading conversation..."):
                ok, data = api_client.get_conversation(conv_id)

            if ok:
                messages = [
                    {
                        "role": m.get("role"),
                        "content": m.get("content"),
                       "citations": m.get("citations", []),   # historical citations aren't returned by this endpoint
                    }
                    for m in data.get("messages", [])
                ]
                set_conversation(conv_id, messages)
                st.rerun()
            else:
                st.error(f"Could not load conversation: {data}")


def render_sidebar():

    st.sidebar.title("Mini Knowledge Base")

    render_upload_section()

    st.sidebar.divider()

    render_search_filters()

    st.sidebar.divider()

    render_documents_section()

    st.sidebar.divider()

    render_conversations_section()
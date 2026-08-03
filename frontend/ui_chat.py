"""
ui_chat.py

Renders the main chat area: welcome screen, message history with
citations, and the bottom question input. Uses Streamlit's native
st.chat_message / st.chat_input, which already look and behave like a
chat app without any custom CSS.
"""

import streamlit as st

import api_client
from config import TOP_K_DEFAULT
from session_state import append_message


def render_welcome_screen():
    st.title("Mini Knowledge Base")
    st.write("Upload a document from the sidebar, then ask a question about it below.")

def render_citations(citations: list):
    if not citations:
        return
    with st.expander("📎 Sources", expanded=False):
        for c in citations:
            title = c.get("title", "Untitled")
            page = c.get("page_number")
            url = c.get("document_url")
            page_text = f" — Page {page}" if page is not None else ""

            if url:
                st.markdown(f"- [**{title}**]({url}){page_text}")
            else:
                st.markdown(f"- **{title}**{page_text}")  # fallback if no URL available

def render_message_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant":
                render_citations(message.get("citations", []))


def handle_new_question(question: str):
    """Send a question to the backend and update session_state with the result."""
    append_message("user", question)

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            ok, result = api_client.post_query(
                question=question,
                conversation_id=st.session_state.current_conversation_id,
                document_id=st.session_state.selected_document_id,
                top_k=TOP_K_DEFAULT,
            )

        if ok:
            answer = result.get("answer", "")
            citations = result.get("citations", [])
            st.write(answer)
            render_citations(citations)

            append_message("assistant", answer, citations)
            st.session_state.current_conversation_id = result.get("conversation_id")

            # Refresh conversation list so a brand-new conversation shows up in the sidebar
            convs_ok, convs = api_client.get_conversations()
            if convs_ok:
                st.session_state.conversations = convs
        else:
            error_text = f"Something went wrong: {result}"
            st.error(error_text)
            append_message("assistant", error_text)


def render_chat_area():
    has_history = len(st.session_state.messages) > 0

    if not has_history and st.session_state.current_conversation_id is None:
        render_welcome_screen()
    else:
        render_message_history()

    question = st.chat_input("Ask a question...")
    if question:
        handle_new_question(question)
        st.rerun()

"""
api_client.py

All communication with the FastAPI backend lives here, and nowhere else.
Every function returns a (ok: bool, data_or_error) tuple so the UI layer
never has to deal with raw exceptions or requests internals.
"""

import requests
from config import BASE_URL, REQUEST_TIMEOUT, UPLOAD_TIMEOUT


def _handle_response(response):
    """Turn a requests Response into (ok, data_or_message)."""
    if response.status_code in (200, 201):
        try:
            return True, response.json()
        except ValueError:
            return False, "Backend returned an invalid response (not JSON)."

    # Try to extract FastAPI's standard error detail, fall back to raw text
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text or f"HTTP {response.status_code}"

    if response.status_code == 400:
        return False, f"Invalid request: {detail}"
    elif response.status_code == 404:
        return False, "Not found. The item may have been removed."
    elif response.status_code == 413:
        return False, f"Too large: {detail}"
    elif response.status_code == 422:
        return False, f"Validation error: {detail}"
    elif response.status_code >= 500:
        return False, "The backend hit an internal error. Please try again."
    else:
        return False, f"Unexpected error ({response.status_code}): {detail}"


def _safe_request(method, url, **kwargs):
    """Wrap a requests call, catching network-level failures."""
    try:
        response = requests.request(method, url, **kwargs)
        return _handle_response(response)
    except requests.exceptions.ConnectionError:
        return False, "Cannot reach the backend. Is it running?"
    except requests.exceptions.Timeout:
        return False, "The request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {e}"


def upload_document(file, document_type: str, department: str | None = None):
    """POST /upload — multipart file upload."""
    files = {"file": (file.name, file.getvalue(), file.type)}
    data = {"document_type": document_type}
    if department:
        data["department"] = department

    return _safe_request(
        "POST",
        f"{BASE_URL}/upload",
        files=files,
        data=data,
        timeout=UPLOAD_TIMEOUT,
    )


def get_documents():
    """GET /documents — list all uploaded documents."""
    return _safe_request("GET", f"{BASE_URL}/documents", timeout=REQUEST_TIMEOUT)


def post_query(
    question: str,
    conversation_id: str | None = None,
    document_id: str | None = None,
    top_k: int = 5,
    document_type: str | None = None,
    department: str | None = None,
):
    """POST /query — ask a question against the knowledge base."""
    payload = {"question": question, "top_k": top_k}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    if document_id:
        payload["document_id"] = document_id
    if document_type:
        payload["document_type"] = document_type
    if department:
        payload["department"] = department

    return _safe_request(
        "POST",
        f"{BASE_URL}/query",
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )


def get_conversations():
    """GET /conversations — list all conversations."""
    return _safe_request("GET", f"{BASE_URL}/conversations", timeout=REQUEST_TIMEOUT)


def get_conversation(conversation_id: str):
    """GET /conversations/{id} — full message history for one conversation."""
    return _safe_request(
        "GET",
        f"{BASE_URL}/conversations/{conversation_id}",
        timeout=REQUEST_TIMEOUT,
    )

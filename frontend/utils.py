"""
utils.py

Small formatting helpers shared across the UI modules.
"""

from datetime import datetime
from zoneinfo import ZoneInfo


def format_timestamp(raw: str | None) -> str:
    """Turn an ISO timestamp string into something readable. Falls back gracefully."""
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(
    raw.replace("Z","+00:00")
)

        dt = dt.astimezone(
            ZoneInfo("Asia/Kolkata")
        )

        return dt.strftime("%b %d, %Y %H:%M")
    except (ValueError, TypeError):
            return raw


def conversation_label(index: int) -> str:
    """Consistent, non-UUID label for a conversation."""
    return f"Conversation {index}"

"""
Central configuration for the Mini Knowledge Base frontend.
Change BASE_URL here if your backend runs on a different host/port.
"""

BASE_URL = "http://fastapi:8000"

REQUEST_TIMEOUT = 30  # seconds, for normal calls
UPLOAD_TIMEOUT = 60   # seconds, uploads/extraction can take longer

DOCUMENT_TYPES = ["general", "resume", "policy", "textbook", "report", "other"]

TOP_K_DEFAULT = 5

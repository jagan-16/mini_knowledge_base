"""
Central configuration for the Mini Knowledge Base frontend.
Change BASE_URL here if your backend runs on a different host/port.
"""

BASE_URL = "http://fastapi:8000"

REQUEST_TIMEOUT = 30  # seconds, for normal calls
UPLOAD_TIMEOUT = 180  # seconds, uploads/extraction can take longer


TOP_K_DEFAULT = 5

"""
Central configuration for the Mini Knowledge Base frontend.
Change BASE_URL here if your backend runs on a different host/port.
"""

BASE_URL = "http://fastapi:8000"

REQUEST_TIMEOUT = 60 # seconds, for normal calls
UPLOAD_TIMEOUT = 600  # seconds, uploads/extraction can take longer


TOP_K_DEFAULT = 5

"""
FaceSecure Web Application - Configuration
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "facesecure-secret-key-super-secure-2026")
    DATABASE_PATH = os.path.join(BASE_DIR, "database", "web_facesecure.db")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "faces")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB max upload
    CONFIDENCE_THRESHOLD = 0.65
    DOOR_UNLOCK_DURATION = 5 # seconds
    COM_PORT = "AUTO"
    BAUD_RATE = 9600

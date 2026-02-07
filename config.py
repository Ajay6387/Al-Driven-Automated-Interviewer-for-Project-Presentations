import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")

# AI Model Settings
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 4096
TEMPERATURE = 0.7

# Interview Settings
MAX_QUESTIONS = 10
MIN_QUESTIONS = 5
FOLLOW_UP_PROBABILITY = 0.6

# Evaluation Weights
EVALUATION_WEIGHTS = {
    "technical_depth": 0.30,
    "clarity": 0.25,
    "originality": 0.25,
    "understanding": 0.20
}

# OCR Settings
OCR_LANG = "eng"
OCR_DPI = 300
OCR_CONFIG = r'--oem 3 --psm 6'

# Audio Settings
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
WHISPER_MODEL = "base"  # Options: tiny, base, small, medium, large

# Session Settings
SESSION_TIMEOUT = 3600  # 1 hour in seconds
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# CORS Settings
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]

# File Storage
UPLOAD_DIR = "uploads"
TEMP_DIR = "temp"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

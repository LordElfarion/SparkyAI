import os
from dotenv import load_dotenv

# Try to load environment variables from .env file
try:
    load_dotenv()
except ImportError:
    print("dotenv not installed, using defaults")

# Debug mode
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

# Secret key for session security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Base directory (absolute path to the project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directory settings
WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Create required directories
os.makedirs(WORKSPACE_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# API settings
API_URL_PREFIX = "/api"

# WebSocket settings
WS_PING_INTERVAL = 30  # seconds

# LLM settings
# Using Ollama API
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent.absolute()

class Settings:
    # Basic app settings
    APP_NAME: str = "SparkyAI"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "An AI assistant powered by Llama3"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # Directory settings
    WORKSPACE_DIR: str = os.path.join(BASE_DIR, "workspace")
    STATIC_DIR: str = os.path.join(BASE_DIR, "static")
    TEMPLATES_DIR: str = os.path.join(BASE_DIR, "templates")
    
    # LLM settings
    LLAMA_MODEL: str = os.getenv("LLAMA_MODEL", "llama3")
    LLAMA_API_URL: str = os.getenv("LLAMA_API_URL", "http://localhost:11434/api/generate")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    USE_OPENAI: bool = os.getenv("USE_OPENAI", "False").lower() == "true"
    
    # Websocket settings
    WS_PING_INTERVAL: int = 30  # seconds
    
    # Browser settings
    HEADLESS_BROWSER: bool = os.getenv("HEADLESS_BROWSER", "True").lower() == "true"
    
    # Additional settings
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Get all settings as a dictionary
    def dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() 
                if not k.startswith('_') and k.isupper()}

# Create settings instance
settings = Settings()
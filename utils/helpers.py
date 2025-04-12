import os
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return str(uuid.uuid4())

def format_timestamp(timestamp: float = None) -> str:
    """Format a timestamp as a readable string"""
    if timestamp is None:
        timestamp = datetime.now().timestamp()
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to be safe for file system operations"""
    # Remove path traversal characters
    sanitized = os.path.basename(filename)
    
    # Replace any potentially problematic characters
    forbidden_chars = ['\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in forbidden_chars:
        sanitized = sanitized.replace(char, '_')
        
    return sanitized

def truncate_text(text: str, max_length: int = 1000, ellipsis: str = "...") -> str:
    """Truncate text to a maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + ellipsis

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON string, returning default if it fails"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def get_file_extension(filename: str) -> str:
    """Get the extension of a file"""
    return os.path.splitext(filename)[1][1:].lower()

def is_url(text: str) -> bool:
    """Check if text is a URL"""
    return text.startswith(('http://', 'https://'))

def retry_decorator(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying a function on exception"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        raise
                    await asyncio.sleep(delay)
            return await func(*args, **kwargs)  # Final attempt
        return wrapper
    return decorator
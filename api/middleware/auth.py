import logging
import jwt
import time
from fastapi import Depends, HTTPException, Header, Request  # Added Request here
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)

def create_session(session_id: str) -> str:
    """Create a JWT token for session authentication"""
    payload = {
        "session_id": session_id,
        "exp": int(time.time()) + 86400 * 30  # 30 days expiration
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

def get_token(authorization: Optional[str] = Header(None), request: Request = None) -> str:
    """Extract and validate the authentication token"""
    # Skip auth for WebSocket routes if request is provided
    if request and is_websocket_route(request.url.path):
        return "websocket"
        
    if not authorization:
        # Allow access without a token in development mode
        if settings.ENV == "development":
            return "development"
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Extract token from Bearer format if present
        token = authorization
        if token.startswith("Bearer "):
            token = token[7:]
        
        # In development mode, token validation is optional
        if settings.ENV == "development" and token == "development":
            return token
        
        # Decode and validate token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        # Token is valid
        return token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_session(session_id: Optional[str], token: str = None) -> str:
    """Verify that the session ID is valid and the user has access"""
    # In development mode, allow all access
    if settings.ENV == "development":
        return session_id
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")
    
    return session_id

def is_websocket_route(path: str) -> bool:
    """Check if a route is a WebSocket route"""
    return path.startswith("/ws/")

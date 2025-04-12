import logging
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any

from config.settings import settings
from config.constants import API_URL_PREFIX
from api.routes import chat, tools, sessions, thinking
from api.middleware.logging import RequestLoggingMiddleware

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION
    )
    
    # Add middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Update for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(chat.router, prefix=f"{API_URL_PREFIX}/chat", tags=["chat"])
    app.include_router(tools.router, prefix=f"{API_URL_PREFIX}/tools", tags=["tools"])
    app.include_router(sessions.router, prefix=f"{API_URL_PREFIX}/sessions", tags=["sessions"])
    app.include_router(thinking.router, prefix=f"{API_URL_PREFIX}/thinking", tags=["thinking"])
    
    # WebSocket connection manager
    app.websocket_connection_manager = WebSocketConnectionManager()
    
    # Add debug WebSocket endpoint
    @app.websocket("/ws/debug")
    async def websocket_debug(websocket: WebSocket):
        """Debug WebSocket endpoint"""
        await websocket.accept()
        await websocket.send_text("WebSocket connection accepted")
        
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(f"You sent: {data}")
        except WebSocketDisconnect:
            logger.info("Debug WebSocket disconnected")
    
    return app

class WebSocketConnectionManager:
    """Manages active WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")
    
    def disconnect(self, client_id: str):
        """Disconnect a WebSocket client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def send_message(self, message: Dict[str, Any], client_id: str = None):
        """
        Send a message to a specific client or broadcast to all
        
        Args:
            message: The message to send
            client_id: Optional client ID to send to (if None, broadcast)
        """
        if client_id:
            # Send to specific client
            if client_id in self.active_connections:
                await self.active_connections[client_id].send_json(message)
        else:
            # Broadcast to all
            for connection in self.active_connections.values():
                await connection.send_json(message)

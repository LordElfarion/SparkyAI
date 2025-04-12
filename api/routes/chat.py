import asyncio
import logging
import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from core.agent import Agent
from config.constants import WS_CHAT_PATH
from api.middleware.auth import get_token, verify_session

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory store of active agents
active_agents: Dict[str, Agent] = {}

class ChatMessage(BaseModel):
    """Model for chat messages"""
    message: str
    session_id: Optional[str] = None

@router.post("/send")
async def send_message(
    chat_message: ChatMessage,
    request: Request,
    token: str = Depends(get_token)
):
    """Send a message to the agent and get a response"""
    # Verify the session if provided
    session_id = chat_message.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
    
    try:
        # Get or create agent for this session
        if session_id not in active_agents:
            websocket_manager = getattr(request.app, "websocket_connection_manager", None)
            active_agents[session_id] = Agent(session_id, websocket_manager)
        
        agent = active_agents[session_id]
        
        # Process the message
        response = await agent.process_message(chat_message.message)
        
        return {
            "status": "success",
            "session_id": session_id,
            "response": response
        }
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.websocket(WS_CHAT_PATH)
async def websocket_chat(websocket: WebSocket, session_id: str = Query(None)):
    """WebSocket endpoint for real-time chat"""
    if not session_id:
        session_id = str(uuid.uuid4())
    
    connection_manager = websocket.app.websocket_connection_manager
    client_id = f"chat_{session_id}"
    
    try:
        await connection_manager.connect(websocket, client_id)
        
        # Get or create agent for this session
        if session_id not in active_agents:
            active_agents[session_id] = Agent(session_id, connection_manager)
        
        agent = active_agents[session_id]
        
        # Send session info
        await websocket.send_json({
            "type": "session_info",
            "session_id": session_id
        })
        
        # Listen for messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", "")
                
                if user_message:
                    # Send acknowledgment
                    await websocket.send_json({
                        "type": "message_received",
                        "message": user_message
                    })
                    
                    # Process the message
                    response = await agent.process_message(user_message)
                    
                    # Send response
                    await websocket.send_json({
                        "type": "agent_response",
                        "message": response
                    })
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message format. Please send JSON."
                })
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                })
    
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            connection_manager.disconnect(client_id)
        except:
            pass
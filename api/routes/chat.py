from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import os
import json
import uuid
import asyncio
from datetime import datetime

# Use absolute imports
from api.websocket import connection_manager
# Import agent modules conditionally
try:
    from agent.base import Agent
    from agent.thinking import ThinkingProcess
    agent_modules_available = True
except ImportError:
    agent_modules_available = False

router = APIRouter()

# Dictionary to store active chat sessions
sessions = {}

@router.post("/chat")
async def create_chat_session():
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    
    # Create session directory
    session_dir = os.path.join("workspace", session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    # Initialize session data
    sessions[session_id] = {
        "id": session_id,
        "created_at": datetime.now().isoformat(),
        "messages": [],
        "thinking": None
    }
    
    return {"session_id": session_id}

@router.post("/chat/{session_id}/message")
async def send_message(session_id: str, message: Dict):
    """Send a message to the AI agent"""
    # Create the session if it doesn't exist
    if session_id not in sessions:
        sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "thinking": None
        }
        # Create session directory
        session_dir = os.path.join("workspace", session_id)
        os.makedirs(session_dir, exist_ok=True)
    
    # Add message to session
    user_message = {
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": message.get("content", ""),
        "timestamp": datetime.now().isoformat()
    }
    sessions[session_id]["messages"].append(user_message)
    
    # Process message with agent if available
    if agent_modules_available:
        try:
            # Create thinking process
            thinking = ThinkingProcess(session_id, connection_manager)
            sessions[session_id]["thinking"] = thinking
            
            # Process message with agent
            agent = Agent(session_id, thinking, connection_manager)
            asyncio.create_task(agent.process_message(user_message))
            
        except Exception as e:
            print(f"Error processing with agent: {str(e)}")
            # Fall back to simple response
            assistant_message = {
                "id": f"assistant-{datetime.now().isoformat()}",
                "role": "assistant",
                "content": f"I received your message, but encountered an error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            sessions[session_id]["messages"].append(assistant_message)
            
            # Send message to client
            asyncio.create_task(
                connection_manager.send_message({
                    "type": "chat_message",
                    "message": assistant_message
                }, session_id)
            )
    else:
        # Create a simple assistant response if agent modules aren't available
        assistant_message = {
            "id": f"assistant-{datetime.now().isoformat()}",
            "role": "assistant",
            "content": "I've received your message, but my processing capabilities are still being configured.",
            "timestamp": datetime.now().isoformat()
        }
        sessions[session_id]["messages"].append(assistant_message)
        
        # Send message to client
        asyncio.create_task(
            connection_manager.send_message({
                "type": "chat_message",
                "message": assistant_message
            }, session_id)
        )
    
    return user_message

@router.get("/chat/{session_id}/messages")
async def get_messages(session_id: str):
    """Get all messages in a chat session"""
    if session_id not in sessions:
        # Return empty messages instead of 404
        return {"messages": []}
    
    return {"messages": sessions[session_id]["messages"]}

@router.get("/chat/list")
async def list_chat_sessions():
    """List all chat sessions"""
    session_list = []
    
    # Add existing sessions
    for session_id, session in sessions.items():
        first_message = ""
        if session["messages"]:
            first_message = session["messages"][0]["content"]
        
        session_list.append({
            "id": session_id,
            "created_at": session["created_at"],
            "message_count": len(session["messages"]),
            "first_message": first_message
        })
    
    # Check for directories in workspace that might be sessions
    workspace_dir = "workspace"
    if os.path.exists(workspace_dir):
        for dir_name in os.listdir(workspace_dir):
            dir_path = os.path.join(workspace_dir, dir_name)
            if os.path.isdir(dir_path) and dir_name not in sessions:
                # Check for conversation.json
                conv_file = os.path.join(dir_path, "conversation.json")
                if os.path.exists(conv_file):
                    try:
                        with open(conv_file, "r") as f:
                            conversation = json.load(f)
                            messages = conversation.get("messages", [])
                            first_message = messages[0]["content"] if messages else ""
                            
                            session_list.append({
                                "id": dir_name,
                                "created_at": datetime.now().isoformat(),  # Use current time as fallback
                                "message_count": len(messages),
                                "first_message": first_message
                            })
                    except:
                        pass
    
    return {"sessions": session_list}

@router.delete("/chat/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session"""
    if session_id in sessions:
        del sessions[session_id]
    
    # Try to delete session directory
    session_dir = os.path.join("workspace", session_id)
    try:
        import shutil
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
    except:
        pass
    
    return {"status": "success"}

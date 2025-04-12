import logging
import json
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio

from config.settings import settings
from config.constants import WS_THINKING_PATH
from api.middleware.auth import get_token, verify_session

logger = logging.getLogger(__name__)

router = APIRouter()

class ThinkingLogRequest(BaseModel):
    """Model for thinking log requests"""
    session_id: str

@router.get("/logs/{session_id}")
async def get_thinking_logs(
    session_id: str,
    token: str = Depends(get_token)
):
    """Get thinking logs for a specific session"""
    # Verify session exists and user has access
    verified_session_id = verify_session(session_id)
    
    try:
        # Get thinking logs directory
        logs_dir = os.path.join(settings.WORKSPACE_DIR, verified_session_id, "thinking")
        
        if not os.path.exists(logs_dir):
            return {
                "status": "success",
                "logs": []
            }
        
        # List log files
        log_files = [f for f in os.listdir(logs_dir) if f.endswith('.json')]
        logs = []
        
        for log_file in log_files:
            try:
                with open(os.path.join(logs_dir, log_file), 'r') as f:
                    log_data = json.load(f)
                    logs.append({
                        "id": log_file.replace(".json", ""),
                        "start_time": log_data.get("start_time"),
                        "end_time": log_data.get("end_time"),
                        "step_count": len(log_data.get("steps", []))
                    })
            except:
                # Skip invalid log files
                continue
        
        # Sort by start time (most recent first)
        logs.sort(key=lambda l: l.get("start_time", 0), reverse=True)
        
        return {
            "status": "success",
            "logs": logs
        }
    except Exception as e:
        logger.error(f"Error getting thinking logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting thinking logs: {str(e)}")

@router.get("/logs/{session_id}/{log_id}")
async def get_thinking_log_detail(
    session_id: str,
    log_id: str,
    token: str = Depends(get_token)
):
    """Get detailed thinking log"""
    # Verify session exists and user has access
    verified_session_id = verify_session(session_id)
    
    try:
        # Get thinking log file
        log_path = os.path.join(settings.WORKSPACE_DIR, verified_session_id, "thinking", f"{log_id}.json")
        
        if not os.path.exists(log_path):
            raise HTTPException(status_code=404, detail=f"Thinking log {log_id} not found")
        
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        return {
            "status": "success",
            "log": log_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thinking log detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting thinking log detail: {str(e)}")

@router.websocket(WS_THINKING_PATH)
async def websocket_thinking(websocket: WebSocket, session_id: str = Query(...)):
    """WebSocket endpoint for real-time thinking updates"""
    connection_manager = websocket.app.websocket_connection_manager
    client_id = f"thinking_{session_id}"
    
    try:
        await connection_manager.connect(websocket, client_id)
        
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id
        })
        
        # Keep connection alive with periodic pings
        while True:
            # Wait for client messages or send periodic pings
            try:
                await asyncio.sleep(30)
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})
            except asyncio.CancelledError:
                break
    
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            connection_manager.disconnect(client_id)
        except:
            pass
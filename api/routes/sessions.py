import logging
import json
import shutil
import uuid
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime


from config.settings import settings
from api.middleware.auth import get_token, create_session, verify_session

logger = logging.getLogger(__name__)

router = APIRouter()

class SessionRequest(BaseModel):
    """Model for session creation requests"""
    name: Optional[str] = None

@router.post("/create")
async def create_new_session(
    session_request: SessionRequest = None,
    token: str = Depends(get_token)
):
    """Create a new session"""
    try:
        # Generate a new session ID
        session_id = str(uuid.uuid4())
        
        # Create session directory
        session_dir = os.path.join(settings.WORKSPACE_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Create session metadata
        session_name = session_request.name if session_request else f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        session_data = {
            "id": session_id,
            "name": session_name,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat()
        }
        
        # Save session metadata
        metadata_path = os.path.join(session_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        # Create auth token for this session
        token = create_session(session_id)
        
        return {
            "status": "success",
            "session": session_data,
            "token": token
        }
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@router.get("/info/{session_id}")
async def get_session_info(
    session_id: str,
    token: str = Depends(get_token)
):
    """Get information about a specific session"""
    try:
        # Verify session exists and user has access
        verified_session_id = verify_session(session_id)
        
        # Get session metadata
        metadata_path = os.path.join(settings.WORKSPACE_DIR, verified_session_id, "metadata.json")
        
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        with open(metadata_path, 'r') as f:
            session_data = json.load(f)
        
        # Update last active timestamp
        session_data["last_active"] = datetime.now().isoformat()
        
        with open(metadata_path, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return {
            "status": "success",
            "session": session_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting session info: {str(e)}")

@router.get("/list")
async def list_sessions(token: str = Depends(get_token)):
    """List all available sessions"""
    try:
        sessions = []
        
        # Iterate through session directories
        workspace_dir = settings.WORKSPACE_DIR
        if os.path.exists(workspace_dir):
            for session_id in os.listdir(workspace_dir):
                metadata_path = os.path.join(workspace_dir, session_id, "metadata.json")
                
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            session_data = json.load(f)
                            sessions.append(session_data)
                    except:
                        # Skip invalid session files
                        continue
        
        # Sort by last active time (most recent first)
        sessions.sort(key=lambda s: s.get("last_active", ""), reverse=True)
        
        return {
            "status": "success",
            "sessions": sessions
        }
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

    @router.delete("/delete/{session_id}")
async def delete_session(
    session_id: str,
    token: str = Depends(get_token)
):
    """Delete a session"""
    try:
        # Verify session exists and user has access
        verified_session_id = verify_session(session_id)
        
        # Get session directory
        session_dir = os.path.join(settings.WORKSPACE_DIR, verified_session_id)
        
        if not os.path.exists(session_dir):
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Delete the session directory
        shutil.rmtree(session_dir)
        
        return {
            "status": "success",
            "message": f"Session {session_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")
    
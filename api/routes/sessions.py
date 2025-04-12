from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import os

# Create router instance
router = APIRouter()

@router.get("/sessions")
async def list_sessions():
    """List all sessions"""
    try:
        sessions = []
        workspace_dir = "workspace"
        
        if os.path.exists(workspace_dir):
            for session_id in os.listdir(workspace_dir):
                session_dir = os.path.join(workspace_dir, session_id)
                if os.path.isdir(session_dir):
                    sessions.append({
                        "id": session_id,
                        "path": session_dir
                    })
        
        return {"sessions": sessions}
    except Exception as e:
        return {"sessions": [], "error": str(e)}

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get details of a specific session"""
    session_dir = os.path.join("workspace", session_id)
    
    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Count files in session
    file_count = 0
    for root, dirs, files in os.walk(session_dir):
        file_count += len(files)
    
    return {
        "id": session_id,
        "path": session_dir,
        "file_count": file_count
    }

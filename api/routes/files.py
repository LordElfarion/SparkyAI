from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import os
import json

# Create router instance
router = APIRouter()

@router.get("/files")
async def list_files():
    """List all available files"""
    try:
        files = []
        workspace_dir = "workspace"
        
        if os.path.exists(workspace_dir):
            for session_id in os.listdir(workspace_dir):
                session_dir = os.path.join(workspace_dir, session_id)
                if os.path.isdir(session_dir):
                    for root, dirs, filenames in os.walk(session_dir):
                        for filename in filenames:
                            file_path = os.path.join(root, filename)
                            rel_path = os.path.relpath(file_path, workspace_dir)
                            files.append({
                                "name": filename,
                                "path": rel_path,
                                "session_id": session_id
                            })
        
        return {"files": files}
    except Exception as e:
        return {"files": [], "error": str(e)}

@router.get("/files/{session_id}")
async def get_session_files(session_id: str):
    """Get files for a specific session"""
    try:
        files = []
        session_dir = os.path.join("workspace", session_id)
        
        if os.path.exists(session_dir):
            for root, dirs, filenames in os.walk(session_dir):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, "workspace")
                    files.append({
                        "name": filename,
                        "path": rel_path
                    })
        
        return {"files": files}
    except Exception as e:
        return {"files": [], "error": str(e)}

@router.get("/files/{session_id}/content")
async def get_file_content(session_id: str, filepath: str):
    """Get content of a specific file"""
    try:
        file_path = os.path.join("workspace", filepath)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"content": content, "path": filepath}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

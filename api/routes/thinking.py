from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import os
import json

router = APIRouter()

@router.get("/thinking/{session_id}")
async def get_thinking_steps(session_id: str):
    """Get thinking steps for a specific session"""
    try:
        thinking_dir = os.path.join("workspace", session_id, "thinking")
        
        if not os.path.exists(thinking_dir):
            return {"steps": []}
        
        # Find the most recent thinking file
        thinking_files = [f for f in os.listdir(thinking_dir) if f.startswith("thinking_") and f.endswith(".json")]
        
        if not thinking_files:
            return {"steps": []}
        
        # Sort by timestamp (which is in the filename)
        thinking_files.sort(reverse=True)
        latest_file = os.path.join(thinking_dir, thinking_files[0])
        
        with open(latest_file, "r") as f:
            thinking_data = json.load(f)
        
        return {"steps": thinking_data.get("steps", [])}
    except Exception as e:
        return {"steps": [], "error": str(e)}

@router.get("/thinking/{session_id}/{thinking_id}")
async def get_thinking_step(session_id: str, thinking_id: str):
    """Get a specific thinking step"""
    try:
        thinking_dir = os.path.join("workspace", session_id, "thinking")
        
        if not os.path.exists(thinking_dir):
            raise HTTPException(status_code=404, detail="Thinking directory not found")
        
        # Find the thinking file containing the step
        thinking_files = [f for f in os.listdir(thinking_dir) if f.startswith("thinking_") and f.endswith(".json")]
        
        for file_name in thinking_files:
            file_path = os.path.join(thinking_dir, file_name)
            with open(file_path, "r") as f:
                thinking_data = json.load(f)
            
            for step in thinking_data.get("steps", []):
                if step.get("id") == thinking_id:
                    return step
        
        raise HTTPException(status_code=404, detail="Thinking step not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

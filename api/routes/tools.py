import logging
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Any, Optional, Union

from config.constants import TOOL_BROWSER, TOOL_SEARCH, TOOL_CODE
from core.agent import Agent
from api.middleware.auth import get_token, verify_session

logger = logging.getLogger(__name__)

router = APIRouter()

class ToolRequest(BaseModel):
    """Model for tool execution requests"""
    tool: str
    input: Union[str, Dict[str, Any]]
    session_id: Optional[str] = None

@router.post("/execute")
async def execute_tool(
    tool_request: ToolRequest,
    request: Request,
    token: str = Depends(get_token)
):
    """Execute a specific tool and return the result"""
    session_id = verify_session(tool_request.session_id)
    
    # Convert input to string if it's a dict
    if isinstance(tool_request.input, dict):
        tool_input = json.dumps(tool_request.input)
    else:
        tool_input = tool_request.input
    
    try:
        # Create a temporary agent for tool execution
        websocket_manager = getattr(request.app, "websocket_connection_manager", None)
        agent = Agent(session_id, websocket_manager)
        
        # Get the requested tool
        if tool_request.tool == TOOL_BROWSER:
            tool = agent.tools["browser"]
        elif tool_request.tool == TOOL_SEARCH:
            tool = agent.tools["search"]
        elif tool_request.tool == TOOL_CODE:
            tool = agent.tools["code"]
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_request.tool}")
        
        # Execute the tool
        result = await tool.execute(tool_input)
        
        return {
            "status": "success",
            "session_id": session_id,
            "tool": tool_request.tool,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error executing tool: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error executing tool: {str(e)}")

@router.get("/list")
async def list_tools(token: str = Depends(get_token)):
    """List available tools and their capabilities"""
    return {
        "status": "success",
        "tools": [
            {
                "id": TOOL_BROWSER,
                "name": "Browser",
                "description": "Navigate websites, take screenshots, and interact with web pages",
                "capabilities": ["navigate", "click", "type_text", "search", "screenshot", "extract_text"]
            },
            {
                "id": TOOL_SEARCH,
                "name": "Search",
                "description": "Search the web for information",
                "capabilities": ["search_web", "search_news", "search_images"]
            },
            {
                "id": TOOL_CODE,
                "name": "Code Executor",
                "description": "Write and execute code",
                "capabilities": ["execute_python", "execute_javascript", "analyze_code"]
            }
        ]
    }
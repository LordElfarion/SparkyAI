import time
import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ThinkingStep:
    def __init__(self, step_id: str, step_type: str, content: str, data: Dict = None):
        self.id = step_id
        self.type = step_type
        self.content = content
        self.data = data or {}
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict:
        """Convert the thinking step to a dictionary"""
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "data": self.data,
            "timestamp": self.timestamp
        }

class ThinkingProcess:
    """
    Manages the thinking process of the agent, tracking the steps taken during reasoning.
    """
    
    def __init__(self, session_id: str, websocket_manager = None):
        self.session_id = session_id
        self.websocket_manager = websocket_manager
        self.steps: List[ThinkingStep] = []
        self.in_progress = True
        self.start_time = time.time()
        self.log_dir = os.path.join("workspace", session_id, "thinking")
        os.makedirs(self.log_dir, exist_ok=True)
        logger.info(f"Initialized thinking process for session {session_id}")
    
    async def add_thinking(self, content: str, data: Dict = None) -> str:
        """Add a thinking step"""
        step = ThinkingStep(f"thinking_{len(self.steps)}", "thinking", content, data)
        self.steps.append(step)
        await self._notify_update(step)
        return step.id
    
    async def add_action(self, content: str, data: Dict = None) -> str:
        """Add an action step"""
        step = ThinkingStep(f"action_{len(self.steps)}", "action", content, data)
        self.steps.append(step)
        await self._notify_update(step)
        return step.id
    
    async def add_result(self, content: str, data: Dict = None) -> str:
        """Add a result step"""
        step = ThinkingStep(f"result_{len(self.steps)}", "result", content, data)
        self.steps.append(step)
        await self._notify_update(step)
        return step.id
    
    async def add_conclusion(self, content: str, data: Dict = None) -> str:
        """Add a conclusion step"""
        step = ThinkingStep(f"conclusion_{len(self.steps)}", "conclusion", content, data)
        self.steps.append(step)
        await self._notify_update(step)
        return step.id
    
    async def complete(self):
        """Mark the thinking process as complete"""
        self.in_progress = False
        await self._save_to_file()
        await self._notify_complete()
    
    async def _notify_update(self, step: ThinkingStep):
        """Send a notification about the new thinking step"""
        if self.websocket_manager:
            await self.websocket_manager.send_message({
                "type": "thinking_update",
                "step": step.to_dict(),
                "session_id": self.session_id
            })
    
    async def _notify_complete(self):
        """Send a notification that thinking is complete"""
        if self.websocket_manager:
            duration = time.time() - self.start_time
            await self.websocket_manager.send_message({
                "type": "thinking_complete",
                "duration": duration,
                "step_count": len(self.steps),
                "session_id": self.session_id
            })
    
    async def _save_to_file(self):
        """Save thinking process to file"""
        try:
            filename = f"thinking_{int(self.start_time)}.json"
            path = os.path.join(self.log_dir, filename)
            
            with open(path, 'w') as f:
                json.dump({
                    "session_id": self.session_id,
                    "start_time": self.start_time,
                    "end_time": time.time(),
                    "steps": [step.to_dict() for step in self.steps]
                }, f, indent=2)
                
            logger.info(f"Saved thinking process to {path}")
            
        except Exception as e:
            logger.error(f"Error saving thinking process: {str(e)}")
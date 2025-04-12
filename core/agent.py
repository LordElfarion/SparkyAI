import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from core.llm.provider import get_llm_provider
from core.memory.conversation import ConversationMemory
from core.thinking import ThinkingProcess
from tools.browser.browser import BrowserAutomation
from tools.web.search import WebSearch
from tools.code.executor import CodeExecutor
from tools.code_generator import CodeGenerator
from tools.file_analyzer import FileAnalyzer
from tools.chat_manager import ChatManager

logger = logging.getLogger(__name__)

class Agent:
    """
    SparkyAI Agent - Core agent functionality
    """
    
    def __init__(self, session_id: str, websocket_manager = None):
        self.session_id = session_id
        self.websocket_manager = websocket_manager
        self.llm = get_llm_provider()
        self.memory = ConversationMemory(session_id)
        self.thinking = None
        self.tools = {
            "browser": BrowserAutomation(session_id, self.notify_update),
            "search": WebSearch(self.notify_update),
            "code": CodeExecutor(session_id, self.notify_update),
            "code_generator": CodeGenerator(session_id, self.notify_update),
            "file_analyzer": FileAnalyzer(session_id, self.notify_update),
            "chat_manager": ChatManager(session_id, self.notify_update)
        }
        self.in_progress = False
        logger.info(f"Initialized agent for session {session_id}")
    
    async def notify_update(self, update_type: str, content: Any):
        """Send updates to the client via websocket"""
        if self.websocket_manager:
            await self.websocket_manager.send_message({
                "type": update_type,
                "content": content,
                "session_id": self.session_id
            })
    
    async def process_message(self, message: str) -> str:
        """Process a user message and generate a response"""
        if self.in_progress:
            return "I'm still processing your previous request. Please wait."
        
        try:
            self.in_progress = True
            await self.notify_update("status", "thinking")
            
            # Add user message to memory
            self.memory.add_message("user", message)
            
            # Initialize thinking process if not exists
            if not self.thinking:
                self.thinking = ThinkingProcess(self.session_id, self.websocket_manager)
            
            # Add thinking step
            await self.thinking.add_thinking(f"User message: {message}\n\nI need to understand what the user is asking and determine the best approach.")
            
            # Determine if we need to use any tools
            tool_choice, tool_input = await self._determine_tool_use(message)
            result = ""
            
            if tool_choice and tool_choice in self.tools:
                # Use the selected tool
                await self.notify_update("status", f"using_tool_{tool_choice}")
                await self.thinking.add_action(f"I'll use the {tool_choice} tool to help with this request.")
                
                tool = self.tools[tool_choice]
                result = await tool.execute(tool_input)
                
                # Add tool result to thinking
                await self.thinking.add_result(f"Result from {tool_choice} tool: {result[:200]}...")
            
            # Generate the final response
            system_prompt = "You are SparkyAI, a helpful and intelligent assistant. You have access to various tools including web browsing, search, and code execution. You can see and interact with web pages."
            
            # Construct prompt with conversation history and any tool results
            conversation_context = self.memory.get_conversation_context()
            prompt = f"{conversation_context}\n\n"
            
            if result:
                prompt += f"I used the {tool_choice} tool and got the following information:\n{result}\n\n"
            
            prompt += f"Based on all available information, I need to provide a comprehensive and helpful response to the user's request: '{message}'"
            
            # Generate response with LLM
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            # Add assistant response to memory
            self.memory.add_message("assistant", response)
            
            # Complete the thinking process
            await self.thinking.add_conclusion(f"My response: {response}")
            await self.thinking.complete()
            
            await self.notify_update("status", "idle")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return f"I'm sorry, but I encountered an error processing your request: {str(e)}"
        finally:
            self.in_progress = False
    
    async def _determine_tool_use(self, message: str) -> tuple[Optional[str], Optional[str]]:
        """Determine if and which tool to use based on the message"""
        system_prompt = """
        Analyze the user message and determine if you need to use a specific tool. 
        Options are:
        1. "browser" - For web browsing, navigating websites, taking screenshots
        2. "search" - For searching the web for information
        3. "code" - For writing and executing code
        4. "none" - If no tool is needed
        
        Output format: {"tool": "selected_tool", "input": "specific input for the tool"}
        """
        
        prompt = f"User message: '{message}'\n\nWhich tool, if any, should I use to best address this request?"
        
        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3  # Lower temperature for more deterministic tool selection
        )
        
        try:
            # Try to parse the JSON response
            parsed_response = json.loads(response)
            tool = parsed_response.get("tool", "none")
            tool_input = parsed_response.get("input", message)
            
            if tool == "none":
                return None, None
                
            return tool, tool_input
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse tool selection JSON: {response}")
            return None, None
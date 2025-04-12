import asyncio
import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, session_id: str, websocket_manager, thinking_process=None):
        self.session_id = session_id
        self.websocket_manager = websocket_manager
        self.workspace_dir = os.path.join("workspace", session_id)
        self.tools = {}  # Will be populated with available tools
        
        # Create workspace directory if it doesn't exist
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        # Initialize thinking process if provided, otherwise create it
        if thinking_process:
            self.thinking = thinking_process
        else:
            # Import here to avoid circular imports
            from agent.thinking import ThinkingProcess
            self.thinking = ThinkingProcess(session_id, websocket_manager)
        
        # Initialize LLM
        try:
            from agent.llm import LlamaLLM
            self.llm = LlamaLLM()
            logger.info(f"LLM initialized for session {session_id}")
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            self.llm = None
        
        # Initialize conversation history
        self.history_file = os.path.join(self.workspace_dir, "conversation.json")
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    self.conversation = json.load(f)
            except:
                self.conversation = {"messages": []}
        else:
            self.conversation = {"messages": []}
    
    async def process_message(self, message: Dict):
        """Process a user message and generate a response"""
        try:
            # Log received message
            logger.info(f"Processing user message: {message['content']}")
            
            # Add user message to conversation if not already there
            if not any(msg.get("id") == message["id"] for msg in self.conversation["messages"]):
                self.conversation["messages"].append({
                    "role": "user",
                    "content": message["content"],
                    "timestamp": message["timestamp"],
                    "id": message["id"]
                })
            
            # Start thinking process
            self.thinking.add_thinking("Received message: {" + message["content"] + "}")
            self.thinking.add_thinking("Processing the message...")
            
            # Generate a simple response
            response_content = ""
            try:
                if self.llm:
                    # Generate response with retry mechanism
                    for attempt in range(3):  # Try up to 3 times
                        try:
                            logger.info(f"Generating response (attempt {attempt+1}/3)")
                            response_content = await self.llm.generate(message["content"])
                            
                            # Check if we got a valid response
                            if response_content and not response_content.startswith("Error:"):
                                break
                            else:
                                logger.warning(f"Invalid response on attempt {attempt+1}: {response_content}")
                                await asyncio.sleep(1)  # Wait before retry
                        except Exception as e:
                            logger.error(f"Error generating response (attempt {attempt+1}): {str(e)}")
                            if attempt == 2:  # Last attempt
                                response_content = f"I'm sorry, I encountered an error while processing your message. Please try again."
                            await asyncio.sleep(1)  # Wait before retry
                else:
                    response_content = "I'm sorry, but the language model is not available. Please check the server logs."
                
                # Log the action
                self.thinking.add_action("Generating response")
            except Exception as e:
                logger.error(f"Failed to generate response: {str(e)}")
                response_content = f"I'm sorry, I encountered an error while processing your message: {str(e)}"
                self.thinking.add_thinking(f"Error: {str(e)}")
            
            # Create assistant message
            assistant_message = {
                "id": f"assistant-{datetime.now().isoformat()}",
                "role": "assistant",
                "content": response_content,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add assistant message to conversation
            self.conversation["messages"].append(assistant_message)
            
            # Save updated conversation
            with open(self.history_file, "w") as f:
                json.dump(self.conversation, f, indent=2)
            
            # Record result in thinking process
            self.thinking.add_result("Response generated")
            
            # Send message to client
            await self.websocket_manager.send_message({
                "type": "chat_message",
                "message": assistant_message
            }, self.session_id)
            
            # Complete thinking process
            self.thinking.add_conclusion("Completed processing the message")
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            
            # Add error to thinking process
            self.thinking.add_thinking(f"Error: {str(e)}")
            self.thinking.add_conclusion(f"Error occurred: {str(e)}")
            
            # Send error message to client
            error_message = {
                "id": f"error-{datetime.now().isoformat()}",
                "role": "assistant",
                "content": f"I'm sorry, an error occurred: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket_manager.send_message({
                "type": "chat_message",
                "message": error_message
            }, self.session_id)
            
            return error_message

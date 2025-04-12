import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ConversationMemory:
    """
    Manages conversation history and provides context for the agent.
    """
    
    def __init__(self, session_id: str, max_history: int = 20):
        self.session_id = session_id
        self.max_history = max_history
        self.messages = []  # List of message dictionaries
        self.storage_dir = os.path.join("workspace", session_id)
        os.makedirs(self.storage_dir, exist_ok=True)
        logger.info(f"Initialized conversation memory for session {session_id}")
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add a message to the conversation history.
        
        Args:
            role: The role of the message sender (user, assistant, system, tool)
            content: The content of the message
            metadata: Optional metadata about the message
        """
        message = {
            "id": f"msg_{len(self.messages)}",
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        
        # Trim history if exceeds max_history
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        
        # Save the updated conversation
        self._save_conversation()
        
        return message
    
    def get_messages(self) -> List[Dict]:
        """Get all messages in the conversation."""
        return self.messages
    
    def get_conversation_context(self, max_tokens: int = 4000) -> str:
        """
        Get the conversation context as a formatted string.
        
        Args:
            max_tokens: Approximate maximum number of tokens to include
        
        Returns:
            Formatted conversation context
        """
        context = "Here is the conversation history:\n\n"
        
        # Start from the most recent messages and work backwards
        for message in reversed(self.messages):
            message_text = f"{message['role'].capitalize()}: {message['content']}\n\n"
            
            # Simple token estimation (very approximate)
            tokens_estimate = len(message_text) / 4
            
            if tokens_estimate > max_tokens:
                # Truncate the message if it's too long
                message_text = message_text[:max_tokens * 4] + "...\n\n"
                context = context + message_text
                break
            
            max_tokens -= tokens_estimate
            context = message_text + context
            
            if max_tokens <= 0:
                break
        
        return context
    
    def clear(self):
        """Clear the conversation history."""
        self.messages = []
        self._save_conversation()
    
    def _save_conversation(self):
        """Save the conversation to disk."""
        try:
            filepath = os.path.join(self.storage_dir, "conversation.json")
            with open(filepath, 'w') as f:
                json.dump({
                    "session_id": self.session_id,
                    "messages": self.messages
                }, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")

import logging
import os
import json
import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class ChatManager:
    """
    Tool for managing chat history, including export
    """
    
    def __init__(self, session_id: str, notify_callback = None):
        self.session_id = session_id
        self.notify_callback = notify_callback
        self.workspace_dir = os.path.join("workspace", session_id)
        os.makedirs(self.workspace_dir, exist_ok=True)
    
    async def execute(self, input_data: str) -> str:
        """Export chat history in various formats"""
        try:
            # Default to exporting as markdown
            export_format = "markdown"
            
            # Check if input specifies a format
            if input_data in ["json", "markdown", "html", "text"]:
                export_format = input_data
            
            # Get conversation file path
            conversation_file = os.path.join(self.workspace_dir, "conversation.json")
            
            if not os.path.exists(conversation_file):
                return "No chat history found for this session"
            
            # Read the conversation data
            with open(conversation_file, "r") as f:
                conversation_data = json.load(f)
            
            # Export based on format
            if export_format == "json":
                # Save to a JSON file
                export_path = os.path.join(self.workspace_dir, f"chat_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                with open(export_path, "w") as f:
                    json.dump(conversation_data, f, indent=2)
                
                return f"Chat history exported to JSON: {export_path}"
                
            elif export_format == "markdown" or export_format == "md":
                # Convert to markdown
                export_path = os.path.join(self.workspace_dir, f"chat_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
                
                with open(export_path, "w") as f:
                    f.write(f"# Chat History - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    for message in conversation_data.get("messages", []):
                        role = message.get("role", "unknown").upper()
                        content = message.get("content", "")
                        timestamp = message.get("timestamp", "")
                        
                        f.write(f"## {role} - {timestamp}\n\n")
                        f.write(f"{content}\n\n")
                        f.write("---\n\n")
                
                return f"Chat history exported to Markdown: {export_path}"
                
            elif export_format == "html":
                # Convert to HTML
                export_path = os.path.join(self.workspace_dir, f"chat_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
                
                with open(export_path, "w") as f:
                    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Chat History</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .message {{ padding: 10px; margin-bottom: 15px; border-radius: 10px; }}
        .user {{ background-color: #e1f5fe; text-align: right; }}
        .assistant {{ background-color: #f5f5f5; }}
        .timestamp {{ font-size: 0.8em; color: #777; }}
    </style>
</head>
<body>
    <h1>Chat History - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h1>
""")
                    
                    for message in conversation_data.get("messages", []):
                        role = message.get("role", "unknown")
                        content = message.get("content", "").replace("\n", "<br>")
                        timestamp = message.get("timestamp", "")
                        
                        f.write(f"""    <div class="message {role}">
        <div class="content">{content}</div>
        <div class="timestamp">{timestamp}</div>
    </div>
""")
                    
                    f.write("</body>\n</html>")
                
                return f"Chat history exported to HTML: {export_path}"
                
            elif export_format == "text" or export_format == "txt":
                # Convert to plain text
                export_path = os.path.join(self.workspace_dir, f"chat_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                
                with open(export_path, "w") as f:
                    f.write(f"Chat History - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    for message in conversation_data.get("messages", []):
                        role = message.get("role", "unknown").upper()
                        content = message.get("content", "")
                        timestamp = message.get("timestamp", "")
                        
                        f.write(f"{role} - {timestamp}\n")
                        f.write(f"{content}\n\n")
                        f.write("-" * 50 + "\n\n")
                
                return f"Chat history exported to Text: {export_path}"
            
            return f"Unsupported export format: {export_format}"
            
        except Exception as e:
            logger.error(f"Chat export error: {str(e)}")
            return f"Error exporting chat: {str(e)}"

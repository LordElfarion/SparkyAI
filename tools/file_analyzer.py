import logging
import os
import json
import base64
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class FileAnalyzer:
    """
    Tool for analyzing uploaded files
    """
    
    def __init__(self, session_id: str, notify_callback = None):
        self.session_id = session_id
        self.notify_callback = notify_callback
        self.workspace_dir = os.path.join("workspace", session_id, "uploaded_files")
        os.makedirs(self.workspace_dir, exist_ok=True)
    
    async def execute(self, input_data: str) -> str:
        """Analyze a file based on its content"""
        try:
            # If input is a base64 encoded file
            if input_data.startswith("data:"):
                # Extract content type and base64 data
                content_parts = input_data.split(',')
                if len(content_parts) > 1:
                    try:
                        # Decode base64 data
                        file_data = base64.b64decode(content_parts[1])
                        
                        # Save to file
                        filename = "uploaded_file.txt"
                        if "image" in content_parts[0]:
                            filename = "uploaded_image.png"
                        
                        file_path = os.path.join(self.workspace_dir, filename)
                        with open(file_path, "wb") as f:
                            f.write(file_data)
                        
                        return f"File saved to {file_path}. Analyzing content..."
                    except:
                        return "Failed to decode file data"
            
            # If input is a file path
            elif os.path.exists(input_data):
                file_path = input_data
                
                # Read the file
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    
                    # Get LLM to analyze the content
                    from core.llm.provider import get_llm_provider
                    llm = get_llm_provider()
                    
                    # Create prompt for file analysis
                    prompt = f"""Analyze the following file content:{content[:5000]} # Limit to first 5000 chars
                    Please provide:
1. A summary of what this content is
2. Key points or structure
3. Any relevant observations"""
                    
                    # Get LLM response
                    analysis = await llm.generate(
                        prompt=prompt,
                        system_prompt="You are an expert file analyzer.",
                        temperature=0.3,
                        max_tokens=2000
                    )
                    
                    return f"## File Analysis: {os.path.basename(file_path)}\n\n{analysis}"
                except:
                    return f"Failed to read or analyze file: {file_path}"
            else:
                # Assume it's text to analyze
                # Get LLM to analyze the content
                from core.llm.provider import get_llm_provider
                llm = get_llm_provider()
                
                # Create prompt for content analysis
                prompt = f"""Analyze the following content:

{input_data[:5000]}  # Limit to first 5000 chars

Please provide a detailed analysis."""
                
                # Get LLM response
                analysis = await llm.generate(
                    prompt=prompt,
                    system_prompt="You are an expert content analyzer.",
                    temperature=0.3,
                    max_tokens=2000
                )
                
                return f"## Content Analysis\n\n{analysis}"
            
        except Exception as e:
            logger.error(f"File analysis error: {str(e)}")
            return f"Error analyzing content: {str(e)}"


import logging
import json
import os
import asyncio
import subprocess
import sys
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class CodeGenerator:
    """
    Tool for generating complete code solutions like Claude does
    """
    
    def __init__(self, session_id: str, notify_callback = None):
        self.session_id = session_id
        self.notify_callback = notify_callback
        self.workspace_dir = os.path.join("workspace", session_id, "generated_code")
        os.makedirs(self.workspace_dir, exist_ok=True)
    
    async def execute(self, input_data: str) -> str:
        """Generate code based on the user's request"""
        try:
            # Get LLM provider
            from core.llm.provider import get_llm_provider
            llm = get_llm_provider()
            
            # Create prompt for code generation
            prompt = f"""Generate complete code for the following request:

{input_data}

Please provide:
1. An explanation of what the code does
2. Well-structured code with comments
3. Instructions for setup and usage

Format your response with markdown headings and code blocks."""
            
            # Get LLM response
            response = await llm.generate(
                prompt=prompt,
                system_prompt="You are an expert software developer. Generate comprehensive, production-ready code with clear explanations.",
                temperature=0.3,
                max_tokens=4000
            )
            
            # Save the generated code to a file
            if "```" in response:
                # Extract code blocks
                import re
                code_blocks = re.findall(r'```(?:\w+)?\s*([\s\S]*?)```', response)
                
                for i, code in enumerate(code_blocks):
                    # Determine the file extension
                    file_ext = ".py"  # Default to Python
                    if "javascript" in response.lower() or "js" in response.lower():
                        file_ext = ".js"
                    elif "html" in response.lower():
                        file_ext = ".html"
                    
                    # Save to file
                    filename = f"generated_code_{i+1}{file_ext}"
                    file_path = os.path.join(self.workspace_dir, filename)
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(code)
                    
                    # Add file path to response
                    response += f"\n\nCode saved to: {file_path}"
            
            return response
            
        except Exception as e:
            logger.error(f"Code generation error: {str(e)}")
            return f"Error generating code: {str(e)}"

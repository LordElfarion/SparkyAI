import os
import sys
import logging
import asyncio
import io
import traceback
import json
import importlib
import contextlib
from typing import Dict, Any, Callable, Optional, Tuple
from typing import Dict, List, Any, Callable, Optional, Tuple

logger = logging.getLogger(__name__)

class CodeExecutor:
    """
    Tool for executing code (primarily Python)
    """
    
    def __init__(self, session_id: str, notify_callback: Callable = None):
        self.session_id = session_id
        self.notify_callback = notify_callback
        self.workspace_dir = os.path.join("workspace", session_id, "code")
        os.makedirs(self.workspace_dir, exist_ok=True)
    
    async def execute_python(self, code: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Execute Python code and return the result
        
        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds
            
        Returns:
            Dictionary with execution results
        """
        # Create StringIO objects to capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Initialize result
        result = {
            "success": False,
            "output": "",
            "error": "",
            "result": None,
            "execution_time": 0
        }
        
        try:
            # Create a global namespace for execution
            namespace = {
                "__builtins__": __builtins__,
                "os": os,
                "sys": sys,
                "json": json,
                "importlib": importlib
            }
            
            # Notify start of execution
            if self.notify_callback:
                await self.notify_callback("code_execution_start", {
                    "language": "python",
                    "code": code
                })
            
            # Execute the code with timeout
            start_time = asyncio.get_event_loop().time()
            
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                # Run the code in a separate task with timeout
                eval_task = asyncio.create_task(self._async_exec(code, namespace))
                exec_result = await asyncio.wait_for(eval_task, timeout=timeout)
            
            end_time = asyncio.get_event_loop().time()
            
# Capture output
            stdout = stdout_capture.getvalue()
            stderr = stderr_capture.getvalue()
            
            # Prepare result
            result["success"] = True
            result["output"] = stdout
            result["error"] = stderr
            result["result"] = exec_result
            result["execution_time"] = end_time - start_time
            
            # Notify completion
            if self.notify_callback:
                await self.notify_callback("code_execution_complete", {
                    "language": "python",
                    "success": True,
                    "output": stdout,
                    "error": stderr,
                    "result": str(exec_result),
                    "execution_time": end_time - start_time
                })
            
            return result
            
        except asyncio.TimeoutError:
            # Handle timeout
            stderr_capture.write("Execution timed out after {timeout} seconds")
            
            result["success"] = False
            result["output"] = stdout_capture.getvalue()
            result["error"] = stderr_capture.getvalue()
            result["execution_time"] = timeout
            
            # Notify timeout
            if self.notify_callback:
                await self.notify_callback("code_execution_complete", {
                    "language": "python",
                    "success": False,
                    "output": result["output"],
                    "error": "Execution timed out",
                    "execution_time": timeout
                })
            
            return result
            
        except Exception as e:
            # Handle other exceptions
            error_msg = traceback.format_exc()
            stderr_capture.write(error_msg)
            
            result["success"] = False
            result["output"] = stdout_capture.getvalue()
            result["error"] = stderr_capture.getvalue()
            
            # Notify error
            if self.notify_callback:
                await self.notify_callback("code_execution_complete", {
                    "language": "python",
                    "success": False,
                    "output": result["output"],
                    "error": error_msg,
                })
            
            return result
    
    async def _async_exec(self, code: str, namespace: Dict) -> Any:
        """Execute code asynchronously and return the result"""
        # Check if the code is a single expression (trying to evaluate)
        try:
            compile(code, "<string>", "eval")
            is_expression = True
        except SyntaxError:
            is_expression = False
            
        # Execute the code
        if is_expression:
            # If it's an expression, evaluate it
            result = eval(code, namespace)
            return result
        else:
            # If it's statements, execute them
            exec(code, namespace)
            # Check for returned value in namespace
            if "__result__" in namespace:
                return namespace["__result__"]
            return None
    
    async def save_file(self, filename: str, content: str) -> bool:
        """
        Save content to a file in the workspace
        
        Args:
            filename: Name of the file to save
            content: Content to write to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure filename doesn't try to access parent directories
            safe_filename = os.path.basename(filename)
            
            # Create file path
            filepath = os.path.join(self.workspace_dir, safe_filename)
            
            # Write content to file
            with open(filepath, 'w') as f:
                f.write(content)
                
            # Notify file saved
            if self.notify_callback:
                await self.notify_callback("file_saved", {
                    "filename": safe_filename,
                    "path": filepath
                })
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {str(e)}")
            return False
    
    async def load_file(self, filename: str) -> Optional[str]:
        """
        Load content from a file in the workspace
        
        Args:
            filename: Name of the file to load
            
        Returns:
            File content if successful, None otherwise
        """
        try:
            # Ensure filename doesn't try to access parent directories
            safe_filename = os.path.basename(filename)
            
            # Create file path
            filepath = os.path.join(self.workspace_dir, safe_filename)
            
            # Check if file exists
            if not os.path.exists(filepath):
                return None
                
            # Read content from file
            with open(filepath, 'r') as f:
                content = f.read()
                
            return content
            
        except Exception as e:
            logger.error(f"Failed to load file {filename}: {str(e)}")
            return None
    
    async def list_files(self) -> List[Dict[str, Any]]:
        """
        List all files in the workspace
        
        Returns:
            List of file information dictionaries
        """
        try:
            files = []
            
            # Iterate through files in the workspace
            for filename in os.listdir(self.workspace_dir):
                filepath = os.path.join(self.workspace_dir, filename)
                
                # Only include files, not directories
                if os.path.isfile(filepath):
                    files.append({
                        "filename": filename,
                        "path": filepath,
                        "size": os.path.getsize(filepath),
                        "modified": os.path.getmtime(filepath)
                    })
                    
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x["modified"], reverse=True)
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []
    
    async def execute(self, input_data: str) -> str:
        """Main execution method for the tool"""
        try:
            # Parse the input as JSON if possible
            try:
                data = json.loads(input_data)
                action = data.get("action", "")
                language = data.get("language", "python")
                code = data.get("code", "")
                filename = data.get("filename", "")
                content = data.get("content", "")
                timeout = int(data.get("timeout", 10))
            except json.JSONDecodeError:
                # If not JSON, assume it's Python code to execute
                action = "execute"
                language = "python"
                code = input_data
                filename = ""
                content = ""
                timeout = 10
            
            # Execute the requested action
            if action == "execute":
                if language == "python":
                    result = await self.execute_python(code, timeout)
                    
                    if result["success"]:
                        return f"Code execution successful:\n\nOutput:\n{result['output']}\n\nResult:\n{result['result']}"
                    else:
                        return f"Code execution failed:\n\nOutput:\n{result['output']}\n\nError:\n{result['error']}"
                else:
                    return f"Unsupported language: {language}"
                    
            elif action == "save":
                if not filename:
                    return "Filename is required for save action"
                    
                success = await self.save_file(filename, content)
                
                if success:
                    return f"File {filename} saved successfully"
                else:
                    return f"Failed to save file {filename}"
                    
            elif action == "load":
                if not filename:
                    return "Filename is required for load action"
                    
                content = await self.load_file(filename)
                
                if content is not None:
                    return f"Content of {filename}:\n\n{content}"
                else:
                    return f"Failed to load file {filename}"
                    
            elif action == "list":
                files = await self.list_files()
                
                if files:
                    response = "Files in workspace:\n\n"
                    for file in files:
                        response += f"- {file['filename']} ({file['size']} bytes)\n"
                    return response
                else:
                    return "No files found in workspace"
                    
            else:
                return f"Unknown action: {action}"
                
        except Exception as e:
            logger.error(f"Code executor error: {str(e)}")
            return f"Code executor error: {str(e)}"
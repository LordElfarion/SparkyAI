#!/usr/bin/env python3
"""
SparkyAI Fix Script
This script fixes common issues found during the initial setup.
"""

import os
import re
import sys

def find_project_root():
    """Find the project root directory"""
    # Look for potential project root locations
    potential_paths = [
        os.path.join(os.getcwd(), "SparkyAI"),  # Current directory + SparkyAI
        os.getcwd(),  # Current directory might be the SparkyAI directory
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "SparkyAI"),  # Script location + SparkyAI
        os.path.dirname(os.path.abspath(__file__)),  # Script location might be the SparkyAI directory
        r"C:\Users\Alex\Desktop\SparkyAI\SparkyAI",  # Path from error message
        r"C:\Users\Alex\Desktop\SparkyAI"  # Parent of path from error message
    ]
    
    # Check each path for app.py file as indicator of project root
    for path in potential_paths:
        app_path = os.path.join(path, "app.py")
        if os.path.exists(app_path):
            print(f"Found project root at: {path}")
            return path
    
    # If no path found, ask user to provide it
    print("Could not automatically find the SparkyAI project directory.")
    user_path = input("Please enter the full path to the SparkyAI project directory: ")
    
    if os.path.exists(os.path.join(user_path, "app.py")):
        return user_path
    else:
        print(f"Error: Could not find app.py in {user_path}")
        print("Please run this script from the SparkyAI project directory or provide the correct path.")
        sys.exit(1)

def fix_conversation_context(file_path):
    """Fix unterminated string in conversation.py"""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Check for the error pattern
        if 'context = "Here is the conversation history:\n\n"' in content and '"\n' not in content[content.find('context = "Here is the conversation history:\n\n"'):content.find('context = "Here is the conversation history:\n\n"') + 50]:
            # Fix the unterminated string
            fixed_content = content.replace(
                'context = "Here is the conversation history:\n\n"',
                'context = "Here is the conversation history:\n\n"\\n\\n"'
            )
            
            with open(file_path, 'w') as file:
                file.write(fixed_content)
            
            print(f"Fixed unterminated string in {file_path}")
        else:
            print(f"No unterminated string found in {file_path} or already fixed")
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")

def fix_missing_import(file_path, import_line, search_pattern):
    """Add missing import to a file"""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        if search_pattern not in content:
            # For adding to import section
            if 'import' in content[:500]:  # Look in first 500 chars
                lines = content.split('\n')
                import_section_end = 0
                
                # Find the end of import section
                for i, line in enumerate(lines):
                    if line.strip().startswith(('import', 'from')) and not line.strip().endswith('\\'):
                        import_section_end = i
                    elif import_section_end > 0 and not line.strip().startswith(('import', 'from')):
                        break
                
                # Insert import after the last import
                lines.insert(import_section_end + 1, import_line)
                fixed_content = '\n'.join(lines)
            else:
                # Add at the beginning if no imports found
                fixed_content = import_line + '\n' + content
            
            with open(file_path, 'w') as file:
                file.write(fixed_content)
            
            print(f"Added missing import to {file_path}")
        else:
            print(f"Import already exists in {file_path}")
    except Exception as e:
        print(f"Error fixing imports in {file_path}: {e}")

def fix_request_parameter(file_path):
    """Fix missing Request type in app.py"""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        modified = False
        
        # Add Request import if missing
        if 'Request' not in content and 'from fastapi import' in content:
            content = content.replace(
                'from fastapi import',
                'from fastapi import Request, '
            )
            modified = True
        
        # Fix the route handler
        if '@app.get("/", response_class=HTMLResponse)' in content and 'request: Request' not in content:
            content = content.replace(
                'async def root(request):',
                'async def root(request: Request):'
            )
            modified = True
        
        if modified:
            with open(file_path, 'w') as file:
                file.write(content)
            print(f"Fixed request parameter in {file_path}")
        else:
            print(f"No issues found in {file_path} or already fixed")
    except Exception as e:
        print(f"Error fixing request parameter in {file_path}: {e}")

def fix_all_python_files(project_root):
    """Examine and fix all Python files in the project"""
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Look for unterminated strings
                    if 'context = "Here is the conversation history:\n\n"' in content and '"\n' not in content[content.find('context = "Here is the conversation history:\n\n"'):content.find('context = "Here is the conversation history:\n\n"') + 50]:
                        fix_conversation_context(file_path)
                    
                    # Look for list import if List type is used
                    if 'List[' in content and 'from typing import' in content and 'List' not in content[content.find('from typing import'):content.find('from typing import') + 100]:
                        if 'from typing import' in content:
                            new_content = re.sub(
                                r'from typing import (.*)',
                                r'from typing import \1, List',
                                content
                            )
                            with open(file_path, 'w') as f:
                                f.write(new_content)
                            print(f"Added List import to {file_path}")
                    
                    # Look for asyncio import if asyncio is used
                    if 'asyncio.' in content and 'import asyncio' not in content:
                        fix_missing_import(file_path, 'import asyncio', 'import asyncio')
                        
                    # Fix request parameter in root functions
                    if file == 'app.py' and '@app.get("/", response_class=HTMLResponse)' in content:
                        fix_request_parameter(file_path)
                        
                except Exception as e:
                    print(f"Error examining {file_path}: {e}")

def main():
    """Main function to fix all issues"""
    project_root = find_project_root()
    
    print(f"Scanning and fixing issues in {project_root}...")
    
    # Core conversation.py
    conversation_path = os.path.join(project_root, "core", "memory", "conversation.py")
    if os.path.exists(conversation_path):
        fix_conversation_context(conversation_path)
    else:
        print(f"Warning: File not found: {conversation_path}")
        
    # Fix executor.py
    executor_path = os.path.join(project_root, "tools", "code", "executor.py")
    if os.path.exists(executor_path):
        fix_missing_import(
            executor_path,
            'from typing import Dict, List, Any, Callable, Optional, Tuple',
            'from typing import Dict, List,'
        )
    else:
        print(f"Warning: File not found: {executor_path}")
    
    # Fix helpers.py
    helpers_path = os.path.join(project_root, "utils", "helpers.py")
    if os.path.exists(helpers_path):
        fix_missing_import(
            helpers_path,
            'import asyncio',
            'import asyncio'
        )
    else:
        print(f"Warning: File not found: {helpers_path}")
    
    # Fix app.py
    app_path = os.path.join(project_root, "app.py")
    if os.path.exists(app_path):
        fix_request_parameter(app_path)
    else:
        print(f"Warning: File not found: {app_path}")
    
    # Scan and fix all Python files
    fix_all_python_files(project_root)
    
    print("\nFixes completed! Try running the application now:")
    print(f"cd {project_root}")
    print("python app.py")

if __name__ == "__main__":
    main()

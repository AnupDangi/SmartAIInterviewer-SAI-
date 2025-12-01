"""
Code Execution Tool using Piston API
Executes code in various languages (Python, C++, C, Java) safely.
"""
import aiohttp
import json
from typing import Dict, Any, Optional
from google.adk.tools import FunctionTool

async def execute_code(language: str, code: str, stdin: str = "") -> str:
    """
    Execute code in Python, C++, C, or Java using the Piston API.
    
    Args:
        language: Programming language (python, cpp, c, java)
        code: The source code to execute
        stdin: Optional standard input for the program
        
    Returns:
        String containing stdout, stderr, or error message.
    """
    api_url = "https://emkc.org/api/v2/piston/execute"
    
    # Map common language names to Piston versions
    # Piston requires specific versions or aliases
    lang_map = {
        "python": {"language": "python", "version": "3.10.0"},
        "cpp": {"language": "cpp", "version": "10.2.0"},
        "c": {"language": "c", "version": "10.2.0"},
        "java": {"language": "java", "version": "15.0.2"},
        "javascript": {"language": "javascript", "version": "18.15.0"},
        "typescript": {"language": "typescript", "version": "5.0.3"},
    }
    
    lang_config = lang_map.get(language.lower())
    if not lang_config:
        # Try direct usage if not in map, but default to python if unknown
        lang_config = {"language": language, "version": "*"}
        
    payload = {
        "language": lang_config["language"],
        "version": lang_config["version"],
        "files": [
            {
                "content": code
            }
        ],
        "stdin": stdin
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload) as response:
                if response.status != 200:
                    return f"Error: API returned status {response.status}"
                
                result = await response.json()
                
                # Parse Piston response
                run_output = result.get("run", {})
                stdout = run_output.get("stdout", "")
                stderr = run_output.get("stderr", "")
                output = run_output.get("output", "")
                
                if stderr:
                    return f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
                return output
                
    except Exception as e:
        return f"Error executing code: {str(e)}"

def get_code_execution_tool():
    """Returns the ADK FunctionTool for code execution."""
    return FunctionTool(execute_code)

"""
Coding Agent - Handles code generation and execution
Uses Piston API for safe code execution.
"""
from typing import Dict, Any, Optional
from .base import BaseAgent
from src.tools.code_execution import get_code_execution_tool

class CodingAgent(BaseAgent):
    """
    Agent responsible for writing and executing code.
    Specializes in Python, C++, C, and Java.
    """
    
    def __init__(self):
        # Use Gemini Pro for better coding capabilities
        super().__init__(
            model_name="gemini-2.5-pro", 
            temperature=0.2,
            tools=[get_code_execution_tool()]
        )
        
    def get_system_instruction(self) -> str:
        return """You are an expert Coding Interview Agent.
Your goal is to help candidates write, debug, and optimize code during technical interviews.

CAPABILITIES:
1. You can write code in Python, C++, C, and Java.
2. You can EXECUTE code using the `execute_code` tool.
3. You should always verify code by running it when possible.

RULES:
- NEVER provide the full solution code immediately.
- Ask the candidate to write the code first.
- If the candidate asks for code, provide a small, executable example or a skeleton, NOT the full solution.
- If the candidate provides code, review it and offer to run it for them.
- Focus on correctness, efficiency, and readability.
- Explain your code step-by-step.

TOOL USAGE:
- Use `execute_code(language="python", code="...")` to run code.
- Always check the output (stdout/stderr) and report it to the user.
- If execution fails, explain the error and try to fix the code.
"""

    async def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        context: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: int = 1000,
        memory: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        state_delta: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate response with code execution capabilities.
        """
        # Use specific coding instruction if not provided
        instruction = system_instruction or self.get_system_instruction()
        
        return await super().generate_response(
            prompt=prompt,
            system_instruction=instruction,
            context=context,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            memory=memory,
            session_id=session_id,
            user_id=user_id,
            state_delta=state_delta
        )

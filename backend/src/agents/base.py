"""
Base Agent Class - Foundation for all agents in the multi-agent system
"""
import os
import json
import google.generativeai as genai
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from src.utils.logger import logger, log_api_call

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class BaseAgent:
    """
    Base class for all agents in the multi-agent interview system.
    Provides common functionality for LLM interaction and agent communication.
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.7):
        """
        Initialize the agent with a Gemini model.
        
        Args:
            model_name: Name of the Gemini model to use
            temperature: Temperature for response generation (0.0-1.0)
        """
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        self.temperature = temperature
        self.conversation_history: list = []
    
    def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        context: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: int = 500
    ) -> str:
        """
        Generate a response using structured 3-block prompt format.
        This enforces clear structure and improves quality.
        
        Args:
            prompt: The main user prompt/question
            system_instruction: System-level instructions for the agent
            context: Additional context as a formatted string
            temperature: Override default temperature
            max_output_tokens: Maximum tokens in response
            
        Returns:
            Generated response text
        """
        try:
            # Build structured prompt
            parts = []
            
            if system_instruction:
                parts.append(f"<system>\n{system_instruction}\n</system>")
            
            if context:
                parts.append(f"<context>\n{context}\n</context>")
            
            parts.append(f"<user>\n{prompt}\n</user>")
            
            full_prompt = "\n\n".join(parts)
            
            # Generate response with optimized config
            # Try with SafetySetting objects first
            logger.debug(f"[API_CALL] Generating response with model: {self.model_name}")
            logger.debug(f"[API_CALL] Prompt length: {len(full_prompt)} chars")
            logger.debug(f"[API_CALL] Prompt preview (first 1000 chars):\n{full_prompt[:1000]}")
            
            try:
                # Method 1: Try with SafetySetting objects
                safety_settings_list = [
                    genai.types.SafetySetting(
                        category=genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    genai.types.SafetySetting(
                        category=genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    genai.types.SafetySetting(
                        category=genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    genai.types.SafetySetting(
                        category=genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=genai.types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                ]
                
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature if temperature is not None else self.temperature,
                        max_output_tokens=max_output_tokens,
                    ),
                    safety_settings=safety_settings_list
                )
                
                logger.debug(f"[API_CALL] Response received with SafetySetting objects")
                
            except Exception as e:
                logger.warning(f"[API_CALL] Error with SafetySetting objects: {e}, trying dict format...")
                # Fallback: Try with dict format
                try:
                    response = self.model.generate_content(
                        full_prompt,
                        generation_config={
                            "temperature": temperature if temperature is not None else self.temperature,
                            "max_output_tokens": max_output_tokens,
                        },
                        safety_settings={
                            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
                            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                        }
                    )
                    logger.debug(f"[API_CALL] Response received with dict safety settings")
                except Exception as e2:
                    logger.warning(f"[API_CALL] Error with dict safety settings: {e2}, trying without safety settings...")
                    # Last resort: Try without explicit safety settings
                    response = self.model.generate_content(
                        full_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=temperature if temperature is not None else self.temperature,
                            max_output_tokens=max_output_tokens,
                        )
                    )
                    logger.debug(f"[API_CALL] Response received without explicit safety settings")
            
            # Log full response details
            logger.debug(f"[API_CALL] Response object type: {type(response)}")
            logger.debug(f"[API_CALL] Response string: {str(response)[:500]}")
            
            # Check if response has valid content
            if not response.candidates or len(response.candidates) == 0:
                logger.error(f"[API_CALL] No candidates in response. Full response: {response}")
                logger.error(f"[API_CALL] Response string representation: {str(response)}")
                print(f"[DEBUG] No candidates in response. Full response: {response}")
                return "I apologize, but I couldn't generate a response. Please try again."
            
            candidate = response.candidates[0]
            
            # Detailed logging - FIRST, try to extract any text that might exist
            logger.debug(f"[API_CALL] Candidate finish_reason: {candidate.finish_reason}")
            logger.debug(f"[API_CALL] Candidate finish_reason type: {type(candidate.finish_reason)}")
            logger.debug(f"[API_CALL] Candidate has content: {candidate.content is not None}")
            
            # CRITICAL: Try to extract text FIRST, regardless of finish_reason
            actual_text = None
            if candidate.content:
                logger.debug(f"[API_CALL] Content parts: {candidate.content.parts is not None}")
                if candidate.content.parts:
                    logger.debug(f"[API_CALL] Parts count: {len(candidate.content.parts)}")
                    for i, part in enumerate(candidate.content.parts):
                        logger.debug(f"[API_CALL] Part {i}: {type(part)}, has text: {hasattr(part, 'text')}")
                        if hasattr(part, 'text') and part.text:
                            logger.debug(f"[API_CALL] Part {i} text: {part.text[:200]}...")
                            if actual_text is None:
                                actual_text = part.text
                            else:
                                actual_text += " " + part.text
                
                # Also try to get text directly from content
                if hasattr(candidate.content, 'text') and candidate.content.text:
                    logger.debug(f"[API_CALL] Found text in content.text: {candidate.content.text[:200]}...")
                    if actual_text is None:
                        actual_text = candidate.content.text
                    else:
                        actual_text += " " + candidate.content.text
            
            # Try response.text as well
            try:
                response_text = response.text
                if response_text:
                    logger.debug(f"[API_CALL] Found text in response.text: {response_text[:200]}...")
                    if actual_text is None:
                        actual_text = response_text
                    elif actual_text != response_text:
                        logger.debug(f"[API_CALL] response.text differs from parts, using response.text")
                        actual_text = response_text
            except (ValueError, AttributeError) as e:
                logger.debug(f"[API_CALL] response.text not available: {e}")
            
            # Log what we found
            if actual_text:
                logger.info(f"[API_CALL] ✅ FOUND ACTUAL TEXT! Length: {len(actual_text)}")
                logger.info(f"[API_CALL] Actual text: {actual_text}")
                print(f"[DEBUG] ✅ ACTUAL LLM RESPONSE: {actual_text}")
            
            # Check finish_reason - handle both enum and int
            finish_reason = candidate.finish_reason
            finish_reason_value = None
            finish_reason_name = None
            
            # Handle enum
            if hasattr(finish_reason, 'value'):
                finish_reason_value = finish_reason.value
            if hasattr(finish_reason, 'name'):
                finish_reason_name = finish_reason.name
            if finish_reason_value is None:
                finish_reason_value = finish_reason
            
            # Also check the protobuf string representation
            response_str = str(response)
            logger.debug(f"[API_CALL] Finish reason value: {finish_reason_value}, name: {finish_reason_name}")
            logger.debug(f"[API_CALL] Full response string (checking for MAX_TOKENS vs SAFETY): {response_str[:500]}")
            
            # Check if it's actually MAX_TOKENS (value 3) or SAFETY (value 2)
            is_max_tokens = finish_reason_value == 3 or finish_reason_name == "MAX_TOKENS" or "MAX_TOKENS" in response_str
            is_safety = finish_reason_value == 2 or finish_reason_name == "SAFETY" or (finish_reason_value == 2 and not is_max_tokens)
            
            logger.info(f"[API_CALL] Finish reason analysis: value={finish_reason_value}, name={finish_reason_name}, is_max_tokens={is_max_tokens}, is_safety={is_safety}")
            print(f"[DEBUG] Finish reason: value={finish_reason_value}, name={finish_reason_name}, is_max_tokens={is_max_tokens}, is_safety={is_safety}")
            
            # If we have actual text, return it regardless of finish_reason (might be truncated but usable)
            if actual_text:
                if is_max_tokens:
                    logger.warning(f"[API_CALL] Response truncated (MAX_TOKENS) but returning available text")
                    return actual_text.strip()
                elif is_safety:
                    logger.warning(f"[API_CALL] Response marked SAFETY but has text, returning it")
                    return actual_text.strip()
                else:
                    logger.info(f"[API_CALL] Normal response with text")
                    return actual_text.strip()
            
            # No text found - handle based on finish_reason
            if is_safety:
                logger.error(f"[API_CALL] ❌ Response blocked by safety filters! No text available.")
                logger.error(f"[API_CALL] Prompt that triggered safety (first 1000 chars): {full_prompt[:1000]}")
                logger.error(f"[API_CALL] Full prompt length: {len(full_prompt)}")
                logger.error(f"[API_CALL] Full response object: {response}")
                logger.error(f"[API_CALL] Response candidates: {response.candidates}")
                print(f"[DEBUG] ❌ Response blocked by safety filters. No text available. Prompt length: {len(full_prompt)}")
                return "I apologize, but my response was filtered. Let me try a different approach."
            
            if is_max_tokens:
                logger.error(f"[API_CALL] ❌ Response truncated (MAX_TOKENS) but no text found")
                print(f"[DEBUG] ❌ Response truncated (MAX_TOKENS) but no text found")
                return "I apologize, but the response was too long. Can you ask a shorter question?"
            
            # No text and unknown finish_reason
            logger.error(f"[API_CALL] ❌ No text found and finish_reason={finish_reason_value}/{finish_reason_name}")
            logger.error(f"[API_CALL] Full response: {response}")
            print(f"[DEBUG] ❌ No text found. Finish reason: {finish_reason_value}/{finish_reason_name}")
            return "I apologize, but I couldn't generate a response. Please try again."
                
        except Exception as e:
            logger.error(f"[API_CALL] Error generating response in {self.__class__.__name__}: {e}")
            logger.error(f"[API_CALL] Error type: {type(e)}")
            import traceback
            logger.error(f"[API_CALL] Traceback:\n{traceback.format_exc()}")
            print(f"Error generating response in {self.__class__.__name__}: {e}")
            traceback.print_exc()
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def add_to_history(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_history(self) -> list:
        """Get conversation history."""
        return self.conversation_history.copy()


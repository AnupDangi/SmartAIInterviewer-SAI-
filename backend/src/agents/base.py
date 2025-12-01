"""
Base Agent Class - REAL Google ADK Implementation
Uses google.adk.agents.LlmAgent and google.adk.runners.Runner
"""
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner, InMemorySessionService
from src.utils.logger import logger
from src.agents.interview_memory import InterviewMemory

load_dotenv()


# Shared session service singleton - ensures sessions persist across agent instances
_shared_session_service = InMemorySessionService()


# ADK Content and Part classes - simple objects with required attributes
class Content:
    """Simple Content object for ADK Runner - must have .role attribute."""
    def __init__(self, role: str, parts: list):
        self.role = role
        self.parts = parts


class Part:
    """Simple Part object for ADK Content - must have .text attribute."""
    def __init__(self, text: str):
        self.text = text


class BaseAgent:
    """
    Base class for all agents using REAL Google ADK.
    Properly creates and manages ADK sessions using Runner.start_session().
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.7, tools: Optional[List[Any]] = None):
        """
        Initialize the agent with ADK LlmAgent.
        
        Args:
            model_name: Name of the Gemini model to use
            temperature: Temperature for response generation (0.0-1.0)
            tools: Optional list of tools to register with the agent
        """
        self.model_name = model_name
        self.temperature = temperature
        self.tools = tools or []
        # Use shared session service so sessions persist across agent instances
        self._session_service = _shared_session_service
        # Use "agents" to match ADK's detected app_name from LlmAgent location
        self._app_name = "agents"
        # Cache for runners (one per system_instruction)
        self._runners: Dict[str, Runner] = {}
        
        logger.info(f"[ADK] Initialized {self.__class__.__name__} with model: {self.model_name}")
    
    def _create_runner(self, system_instruction: Optional[str] = None) -> Runner:
        """
        Create ADK Runner instance for the given system instruction.
        Caches runners by system_instruction key.
        
        Args:
            system_instruction: Optional system instruction for the agent
            
        Returns:
            Runner instance
        """
        cache_key = f"{self.model_name}_{system_instruction or 'default'}"
        
        if cache_key not in self._runners:
            # Create LlmAgent
            agent_data = {
                "model": self.model_name,
                "name": self.__class__.__name__.lower().replace("agent", ""),
            }
            
            if system_instruction:
                agent_data["instruction"] = system_instruction
                
            if self.tools:
                agent_data["tools"] = self.tools
            
            llm_agent = LlmAgent(**agent_data)
            
            # Create Runner with shared session service
            runner = Runner(
                app_name=self._app_name,
                agent=llm_agent,
                session_service=self._session_service
            )
            
            self._runners[cache_key] = runner
            logger.debug(f"[ADK] Created Runner for {self.__class__.__name__} with model: {self.model_name}")
        
        return self._runners[cache_key]
    
    async def _ensure_session_exists(
        self,
        session_id: str,
        user_id: str,
        initial_state: Optional[Dict[str, Any]] = None
    ):
        """
        Ensure ADK session exists before using it with run_async.
        Creates session using session_service.create_session() if it doesn't exist.
        
        Args:
            session_id: Session ID (session_run_id)
            user_id: User ID
            initial_state: Optional initial state for new sessions
            
        Returns:
            Session object if exists or created, None if error
        """
        try:
            # Try to get existing session using session service
            session = await self._session_service.get_session(
                app_name=self._app_name,
                user_id=user_id,
                session_id=session_id
            )
            logger.debug(f"[ADK] Session {session_id} already exists in service {id(self._session_service)}")
            # Debug: Check if session is actually in the internal storage if possible
            if hasattr(self._session_service, '_sessions'):
                 logger.debug(f"[ADK] Service sessions keys: {list(self._session_service._sessions.keys())}")
            return session
        except (ValueError, KeyError, AttributeError, Exception) as e:
            # Session doesn't exist - create it using session_service.create_session()
            logger.debug(f"[ADK] Session {session_id} not found, creating new session using session_service.create_session()")
            try:
                # Try different parameter combinations for create_session
                try:
                    # Try with all parameters first
                    session = await self._session_service.create_session(
                        app_name=self._app_name,
                        user_id=user_id,
                        session_id=session_id,
                        state=initial_state or {}
                    )
                except (TypeError, AttributeError):
                    # Try without state parameter
                    try:
                        session = await self._session_service.create_session(
                            app_name=self._app_name,
                            user_id=user_id,
                            session_id=session_id
                        )
                        # Set state separately if session has state attribute
                        if initial_state and hasattr(session, 'state'):
                            session.state.update(initial_state)
                    except (TypeError, AttributeError):
                        # Try with minimal parameters (app_name and user_id only)
                        session = await self._session_service.create_session(
                            app_name=self._app_name,
                            user_id=user_id
                        )
                        # Set state separately if session has state attribute
                        if initial_state and hasattr(session, 'state'):
                            session.state.update(initial_state)
                
                logger.info(f"[ADK] ✅ Successfully created session {session_id} for user {user_id}")
                return session
            except Exception as create_error:
                logger.error(f"[ADK] Failed to create session using session_service.create_session(): {create_error}")
                # Don't raise - let run_async handle session creation if needed
                return None
    
    def switch_model(self, new_model_name: str):
        """Switch to a different model dynamically"""
        if new_model_name != self.model_name:
            logger.info(f"[ADK] Switching model from {self.model_name} to {new_model_name}")
            self.model_name = new_model_name
            # Clear runner cache so new model is used
            self._runners.clear()
    
    async def _run_with_adk(
        self,
        prompt: str,
        session_id: str,
        user_id: str,
        system_instruction: Optional[str] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        state_delta: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Run agent with ADK, ensuring session exists before calling run_async.
        
        Args:
            prompt: The user prompt/question
            session_id: Session ID (session_run_id)
            user_id: User ID
            system_instruction: Optional system instruction
            initial_state: Optional initial state for session creation
            state_delta: Optional state updates to apply
            
        Returns:
            Generated response text
        """
        # Create runner
        runner = self._create_runner(system_instruction=system_instruction)
        
        # Ensure session exists (create if needed) - use session service directly
        await self._ensure_session_exists(
            session_id=session_id,
            user_id=user_id,
            initial_state=initial_state
        )
        
        # Debug Runner state
        # Ensure session exists in the runner's service
        # This handles cases where the runner might be using a different service instance or key
        service = getattr(runner, 'session_service', None)
        if service:
            try:
                await service.create_session(
                    app_name=getattr(runner, 'app_name', 'agents'),
                    user_id=user_id,
                    session_id=session_id,
                    state=initial_state or {}
                )
            except Exception:
                # Session likely already exists, which is fine
                pass
        
        # Create Content object for ADK
        new_message = Content(role="user", parts=[Part(text=prompt)])
        
        # Run agent - session now exists
        response_text = ""
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message,
                state_delta=state_delta
            ):
                # Collect text from response events
                if hasattr(event, 'text') and event.text:
                    response_text += event.text
                elif hasattr(event, 'content') and event.content:
                    if isinstance(event.content, str):
                        response_text += event.content
                    elif hasattr(event.content, 'text'):
                        response_text += event.content.text
                    elif hasattr(event.content, 'parts'):
                        # Handle parts list
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
                elif hasattr(event, 'message') and event.message:
                    if hasattr(event.message, 'content'):
                        if isinstance(event.message.content, str):
                            response_text += event.message.content
                        elif hasattr(event.message.content, 'text') and event.message.content.text:
                            response_text += event.message.content.text
                        elif hasattr(event.message.content, 'parts'):
                            for part in event.message.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_text += part.text
        except Exception as e:
            import sys
            sys.stderr.write(f"[ADK-DEBUG] Error in run_async loop: {e}\n")
            # Re-raise to be handled by caller
            raise e
        
        return response_text.strip()
    
    async def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        context: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: int = 300,
        memory: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        state_delta: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response using Google ADK Runner.
        Properly creates ADK sessions using runner.start_session() before calling run_async.
        
        Args:
            prompt: The main user prompt/question
            system_instruction: System-level instructions for the agent
            context: Additional context as a formatted string
            temperature: Override default temperature (not used, kept for compatibility)
            max_output_tokens: Maximum tokens in response (not used, kept for compatibility)
            memory: Optional DB memory dict (CV/JD summaries) - included in context
            session_id: Session ID for ADK session management
            user_id: User ID for ADK session management
            state_delta: Optional state updates to apply
            
        Returns:
            Generated response text
        """
        try:
            # Build full message with context
            context_parts = []
            
            if memory:
                memory_str = "\n".join([f"{k}: {str(v)[:200]}" for k, v in memory.items() if v])
                if memory_str:
                    context_parts.append(f"DB CONTEXT:\n{memory_str}")
            
            if context:
                context_parts.append(context)
            
            full_context = "\n\n".join(context_parts) if context_parts else ""
            user_message = f"{full_context}\n\n{prompt}" if full_context else prompt
            
            logger.debug(f"[ADK] Generating response with model: {self.model_name}")
            logger.debug(f"[ADK] System instruction: {bool(system_instruction)}")
            logger.debug(f"[ADK] User message length: {len(user_message)} chars")
            logger.debug(f"[ADK] Session ID: {session_id}")
            
            # Use ADK's proper async execution
            user_id_for_adk = user_id or "default_user"
            session_id_for_adk = session_id or "default_session"
            
            # Use state_delta as initial state if provided for new sessions
            initial_state = state_delta if state_delta else {}
            
            # Retry loop for 503 errors
            max_retries = 3
            import asyncio
            
            for attempt in range(max_retries):
                try:
                    # Run with ADK - this will create session if needed
                    response_text = await self._run_with_adk(
                        prompt=user_message,
                        session_id=session_id_for_adk,
                        user_id=user_id_for_adk,
                        system_instruction=system_instruction,
                        initial_state=initial_state,
                        state_delta=state_delta
                    )
                    
                    result = response_text if response_text else "I apologize, but I couldn't generate a response. Please try again."
                    
                    logger.info(f"[ADK] ✅ Successfully generated response ({len(result)} chars)")
                    return result
                    
                except Exception as e:
                    error_str = str(e)
                    is_overloaded = "503" in error_str or "overloaded" in error_str.lower()
                    
                    if is_overloaded and attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # 1s, 2s, 4s
                        logger.warning(f"[ADK] Model overloaded (503). Retrying in {wait_time}s (Attempt {attempt+1}/{max_retries})...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    # If not overloaded or last retry, raise to outer handler
                    raise e
            
        except Exception as e:
            # Check for specific Google API errors
            error_str = str(e)
            if "503" in error_str or "overloaded" in error_str.lower():
                logger.warning(f"[ADK] Model overloaded (503) after retries.")
                return "I'm currently experiencing very high traffic. Please give me a moment and try asking again."
            
            if "429" in error_str or "quota" in error_str.lower():
                logger.warning(f"[ADK] Quota exceeded (429).")
                return "I've reached my usage limit for the moment. Please try again in a minute."
                
            logger.error(f"[ADK] Error generating response in {self.__class__.__name__}: {e}")
            import traceback
            logger.error(f"[ADK] Traceback:\n{traceback.format_exc()}")
            return "I apologize, but I encountered a temporary issue. Please try again."
    
    async def get_session_memory(self, session_id: str, user_id: str) -> Optional[InterviewMemory]:
        """
        Get in-session memory from ADK session state.
        
        Args:
            session_id: The session_run_id
            user_id: User identifier
            
        Returns:
            InterviewMemory object or None
        """
        try:
            # Get session using session service directly
            try:
                session = await self._session_service.get_session(
                    app_name=self._app_name,
                    user_id=user_id,
                    session_id=session_id
                )
                
                # Extract state from session
                if hasattr(session, 'state') and session.state:
                    memory = InterviewMemory.from_dict(dict(session.state))
                    return memory
            except (ValueError, KeyError, AttributeError):
                # Session doesn't exist yet - that's okay
                pass
            
            return None
        except Exception as e:
            logger.debug(f"[ADK] Could not retrieve session memory: {e}")
            return None
    
    def set_session_memory(
        self,
        session_id: str,
        user_id: str,
        memory: InterviewMemory
    ):
        """
        Update ADK session state with InterviewMemory.
        Note: State is primarily managed via state_delta in generate_response.
        
        Args:
            session_id: The session_run_id
            user_id: User identifier
            memory: InterviewMemory object to store
        """
        try:
            # ADK manages state through state_delta in run_async
            # This method is kept for compatibility
            logger.debug(f"[ADK] Session state managed by ADK Runner via state_delta")
        except Exception as e:
            logger.error(f"[ADK] Error setting session memory: {e}")
    
    def reset_session(self, session_id: str, user_id: str):
        """Reset/delete ADK session (start new interview run)"""
        try:
            # TODO: Implement session deletion if needed
            logger.info(f"[ADK] Session reset requested for {session_id}")
        except Exception as e:
            logger.warning(f"[ADK] Error resetting session: {e}")
    
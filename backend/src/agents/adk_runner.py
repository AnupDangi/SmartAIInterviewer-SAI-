"""
PHASE 1: ADK Runner Setup
Pure ADK Runner configuration - single instance, shared session service
"""
from google.adk.runners import Runner, InMemorySessionService
from google.adk.agents import LlmAgent
from google.genai import types
from typing import Optional, Dict, Any
from src.agents.adk_coordinator import create_coordinator_agent
from src.utils.logger import logger

# Shared session service - persists across all requests
_session_service = InMemorySessionService()

# Shared runner instance
_runner: Optional[Runner] = None


def get_adk_runner() -> Runner:
    """
    Get or create the shared ADK Runner instance
    Singleton pattern - one runner for the entire app
    """
    global _runner
    
    if _runner is None:
        # Create the coordinator agent (pure ADK LlmAgent)
        coordinator = create_coordinator_agent(model_name="gemini-2.5-flash")
        
        # Create ADK Runner
        _runner = Runner(
            app_name="interviewer",
            agent=coordinator,
            session_service=_session_service
        )
        
        logger.info("[ADK] ✅ Created shared ADK Runner instance")
    
    return _runner


def get_session_service() -> InMemorySessionService:
    """Get the shared session service"""
    return _session_service


async def create_session(
    user_id: str,
    session_id: str,
    initial_state: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Create an ADK session
    
    Args:
        user_id: User identifier
        session_id: Session identifier (session_run_id)
        initial_state: Optional initial state
        
    Returns:
        ADK Session object
    """
    session_service = get_session_service()
    
    try:
        # Try to get existing session first
        session = await session_service.get_session(
            app_name="interviewer",
            user_id=user_id,
            session_id=session_id
        )
        logger.debug(f"[ADK] Session {session_id} already exists")
        return session
    except (ValueError, KeyError):
        # Create new session
        logger.info(f"[ADK] Creating new session {session_id} for user {user_id}")
        session = await session_service.create_session(
            app_name="interviewer",
            user_id=user_id,
            session_id=session_id,
            state=initial_state or {}
        )
        logger.info(f"[ADK] ✅ Session {session_id} created successfully")
        return session


async def run_agent(
    user_id: str,
    session_id: str,
    user_message: str,
    state_delta: Optional[Dict[str, Any]] = None
) -> str:
    """
    Run the coordinator agent with a user message
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        user_message: User's message
        state_delta: Optional state updates
        
    Returns:
        Agent response text
    """
    runner = get_adk_runner()
    
    # Create Content object for ADK
    content = types.Content(
        role="user",
        parts=[types.Part(text=user_message)]
    )
    
    # Run agent using ADK Runner
    response_text = ""
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
        state_delta=state_delta
    ):
        # Collect text from response events
        if hasattr(event, 'message') and event.message:
            if hasattr(event.message, 'content'):
                if isinstance(event.message.content, str):
                    response_text += event.message.content
                elif hasattr(event.message.content, 'parts'):
                    for part in event.message.content.parts:
                        if hasattr(part, 'text'):
                            response_text += part.text
                elif hasattr(event.message.content, 'text'):
                    response_text += event.message.content.text
        elif hasattr(event, 'text') and event.text:
            response_text += event.text
        elif hasattr(event, 'content') and event.content:
            if isinstance(event.content, str):
                response_text += event.content
            elif hasattr(event.content, 'text'):
                response_text += event.content.text
    
    return response_text.strip()


async def get_session_state(
    user_id: str,
    session_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get current session state
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        
    Returns:
        Session state dictionary or None
    """
    session_service = get_session_service()
    
    try:
        session = await session_service.get_session(
            app_name="interviewer",
            user_id=user_id,
            session_id=session_id
        )
        
        # Return session state
        if hasattr(session, 'state'):
            return dict(session.state) if session.state else {}
        
        return None
    except (ValueError, KeyError):
        return None


"""
Logging utility for the application
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Create logs directory if it doesn't exist
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log file path
LOG_FILE = LOG_DIR / "app.log"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger("sai_interviewer")

def log_api_call(agent_name: str, prompt: str, response: Any, error: Optional[Exception] = None):
    """Log API call details"""
    logger.debug(f"[API_CALL] Agent: {agent_name}")
    logger.debug(f"[API_CALL] Prompt length: {len(prompt)}")
    logger.debug(f"[API_CALL] Prompt preview: {prompt[:500]}...")
    
    if error:
        logger.error(f"[API_CALL] Error: {error}")
    else:
        logger.debug(f"[API_CALL] Response type: {type(response)}")
        if hasattr(response, 'candidates'):
            logger.debug(f"[API_CALL] Candidates count: {len(response.candidates) if response.candidates else 0}")
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                logger.debug(f"[API_CALL] Finish reason: {candidate.finish_reason}")
                logger.debug(f"[API_CALL] Has content: {candidate.content is not None}")
                if candidate.content:
                    logger.debug(f"[API_CALL] Parts count: {len(candidate.content.parts) if candidate.content.parts else 0}")
        logger.debug(f"[API_CALL] Full response object: {response}")


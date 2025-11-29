"""
Memory Agent - Manages interview session memory and conversation continuity
"""
from typing import Dict, Any, List, Optional
from .base import BaseAgent
from sqlalchemy.orm import Session
from src.db.models import InterviewSession


class MemoryAgent(BaseAgent):
    """
    Memory Agent manages:
    - In-session memory (short-term)
    - Key points extraction
    - Conversation continuity
    - Long-term memory persistence
    """
    
    def __init__(self):
        super().__init__(model_name="gemini-2.5-flash", temperature=0.5)
    
    def extract_key_points(
        self,
        conversation_turn: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Extract key points from a conversation turn.
        
        Args:
            conversation_turn: Dictionary with 'ai_message' and 'user_message'
            
        Returns:
            Extracted key points and insights
        """
        system_instruction = """You are a memory agent. Extract key information from interview conversations:
- Skills mentioned
- Experience details
- Technical knowledge demonstrated
- Strengths and weaknesses
- Areas to probe deeper"""
        
        prompt = f"""Extract key points from this conversation turn:

AI: {conversation_turn.get('ai_message', '')}
Candidate: {conversation_turn.get('user_message', '')}

Extract:
1. Key skills mentioned
2. Experience details
3. Technical knowledge shown
4. Areas that need follow-up"""
        
        response = self.generate_response(prompt, system_instruction)
        
        return {
            "extracted_points": response,
            "conversation_turn": conversation_turn
        }
    
    def build_session_summary(
        self,
        interview_id: str,
        db: Session
    ) -> str:
        """
        Build a summary of the interview session so far.
        
        Args:
            interview_id: UUID of the interview
            db: Database session
            
        Returns:
            Session summary string
        """
        sessions = db.query(InterviewSession).filter(
            InterviewSession.interview_id == interview_id
        ).order_by(InterviewSession.created_at.asc()).all()
        
        if not sessions:
            return "Interview just started. No conversation yet."
        
        conversation = "\n".join([
            f"Q: {s.ai_message}\nA: {s.user_message}"
            for s in sessions
        ])
        
        system_instruction = """You are a memory agent. Create a concise summary of the interview session."""
        
        prompt = f"""Summarize this interview conversation:

{conversation}

Create a brief summary (3-4 sentences) covering:
- Topics discussed
- Candidate's key responses
- Skills demonstrated
- Areas covered"""
        
        summary = self.generate_response(prompt, system_instruction)
        return summary
    
    def get_conversation_context(
        self,
        interview_id: str,
        limit: int,
        db: Session
    ) -> List[Dict[str, str]]:
        """
        Get recent conversation context for continuity.
        
        Args:
            interview_id: UUID of the interview
            limit: Number of recent turns to retrieve
            db: Database session
            
        Returns:
            List of conversation turns
        """
        sessions = db.query(InterviewSession).filter(
            InterviewSession.interview_id == interview_id
        ).order_by(InterviewSession.created_at.desc()).limit(limit).all()
        
        sessions.reverse()  # Chronological order
        
        return [
            {
                "ai_message": s.ai_message,
                "user_message": s.user_message,
                "feedback": s.feedback
            }
            for s in sessions
        ]


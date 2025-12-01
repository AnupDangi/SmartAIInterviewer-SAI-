"""
Interview Memory - In-session memory for interview state tracking
Pydantic BaseModel for ADK compatibility (< 5 KB), session-only (not persisted to DB)
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json


class InterviewMemory(BaseModel):
    """
    In-session memory object for interview state (ADK-compatible Pydantic model).
    Lives only during the session, not persisted to DB.
    Kept under 5 KB - only summaries and scalars.
    """
    stage: str = Field(default="intro", description="Interview stage: intro → technical → behavioral → closing")
    question_count: int = Field(default=0, description="Number of questions asked")
    last_answer_depth: float = Field(default=0.5, description="Depth score of last answer (0.0-1.0)")
    topics_covered: List[str] = Field(default_factory=list, description="List of topics covered")
    candidate_name: str = Field(default="there", description="Candidate's name")
    cv_summary: Optional[str] = Field(default=None, description="Summary of the candidate's CV")
    job_description: Optional[str] = Field(default=None, description="The job description")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Session start time")
    duration_minutes: int = Field(default=30, description="Total interview duration in minutes")
    
    class Config:
        """Pydantic config for ADK compatibility."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (Pydantic method)."""
        return self.model_dump(exclude_none=True)
    
    def to_json(self) -> str:
        """Convert to JSON string for context passing."""
        return self.model_dump_json(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterviewMemory":
        """Load from dictionary (Pydantic method)."""
        return cls(**data)
    
    def update_stage(self, duration_minutes: int = 30):
        """Update stage based on elapsed time and question count."""
        # Calculate elapsed time
        elapsed_minutes = (datetime.utcnow() - self.start_time).total_seconds() / 60.0
        
        # Time-based thresholds
        if elapsed_minutes >= duration_minutes * 0.9:
            self.stage = "closing"
            return
        elif elapsed_minutes >= duration_minutes * 0.7:
            self.stage = "behavioral"
            return
            
        # Question-based thresholds (fallback/pacing)
        total_questions = duration_minutes // 3  # Assume ~3 mins per question
        
        if self.question_count == 0:
            self.stage = "intro"
        elif self.question_count <= 1: # Intro is usually just 1 question
            self.stage = "intro"
        elif self.question_count <= total_questions * 0.7:
            self.stage = "technical"
        elif self.question_count <= total_questions * 0.9:
            self.stage = "behavioral"
        else:
            self.stage = "closing"
    
    def increment_question(self, duration_minutes: int):
        """Increment question count and update stage."""
        self.question_count += 1
        self.update_stage(duration_minutes)
    
    def add_topic(self, topic: str):
        """Add a covered topic (keep list small)."""
        if topic and topic not in self.topics_covered:
            self.topics_covered.append(topic)
            # Keep only last 10 topics to stay under 5 KB
            if len(self.topics_covered) > 10:
                self.topics_covered = self.topics_covered[-10:]
    
    def get_size_kb(self) -> float:
        """Get approximate memory size in KB."""
        json_str = self.to_json()
        return len(json_str.encode('utf-8')) / 1024.0


"""
PHASE 1: ADK Interview State
Pure ADK State definition for interview session state
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class InterviewState(BaseModel):
    """
    ADK Session State for Interview
    Lives in ADK session.state automatically
    """
    stage: str = Field(default="intro", description="Interview stage: intro → technical → behavioral → closing")
    question_count: int = Field(default=0, description="Number of questions asked")
    last_answer_depth: float = Field(default=0.5, description="Depth score of last answer (0.0-1.0)")
    topics_covered: List[str] = Field(default_factory=list, description="List of topics covered")
    candidate_name: str = Field(default="Candidate", description="Candidate's name")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for ADK session state"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: dict) -> "InterviewState":
        """Create from dictionary (from ADK session state)"""
        return cls(**data) if data else cls()
    
    def update_stage(self, duration_minutes: int):
        """Update stage based on question count and duration"""
        total_questions = duration_minutes // 2
        
        if self.question_count == 0:
            self.stage = "intro"
        elif self.question_count <= total_questions * 0.3:
            self.stage = "intro"
        elif self.question_count <= total_questions * 0.7:
            self.stage = "technical"
        elif self.question_count <= total_questions * 0.9:
            self.stage = "behavioral"
        else:
            self.stage = "closing"
    
    def increment_question(self, duration_minutes: int):
        """Increment question count and update stage"""
        self.question_count += 1
        self.update_stage(duration_minutes)


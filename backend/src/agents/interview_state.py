"""
Interview State Machine - Tracks interview progress and context
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InterviewState:
    """
    State machine for tracking interview progress.
    This enables adaptive, stage-aware questioning.
    """
    stage: str = "intro"  # intro → technical → behavioral → closing
    question_count: int = 0
    topics_covered: List[str] = field(default_factory=list)
    current_topic: Optional[str] = None
    candidate_name: str = "there"
    cv_highlights: List[str] = field(default_factory=list)
    jd_requirements: List[str] = field(default_factory=list)
    summary_so_far: str = ""
    last_answer_depth: float = 0.5
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "stage": self.stage,
            "question_count": self.question_count,
            "topics_covered": self.topics_covered,
            "current_topic": self.current_topic,
            "candidate_name": self.candidate_name,
            "cv_highlights": self.cv_highlights,
            "jd_requirements": self.jd_requirements,
            "summary_so_far": self.summary_so_far,
            "last_answer_depth": self.last_answer_depth,
        }
    
    def update_stage(self, duration_minutes: int):
        """Update stage based on question count and duration."""
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
        """Increment question count and update stage."""
        self.question_count += 1
        self.update_stage(duration_minutes)
    
    def add_topic(self, topic: str):
        """Add a covered topic."""
        if topic and topic not in self.topics_covered:
            self.topics_covered.append(topic)
    
    def update_summary(self, summary: str):
        """Update conversation summary."""
        self.summary_so_far = summary


def answer_depth(answer: str) -> float:
    """
    Calculate answer depth score (0.0 - 1.0).
    Higher score = more detailed, technical, thoughtful answer.
    
    Args:
        answer: Candidate's answer text
        
    Returns:
        Depth score between 0.0 and 1.0
    """
    if not answer or len(answer.strip()) < 20:
        return 0.2
    
    answer_lower = answer.lower()
    score = 0.5  # Base score
    
    # Length indicators
    word_count = len(answer.split())
    if word_count < 30:
        score -= 0.2
    elif word_count > 100:
        score += 0.2
    elif word_count > 200:
        score += 0.3
    
    # Technical indicators
    technical_keywords = [
        "time complexity", "space complexity", "o(n)", "o(log n)",
        "scalable", "scalability", "optimization", "tradeoff", "trade-off",
        "architecture", "design pattern", "algorithm", "data structure",
        "distributed", "concurrent", "async", "threading", "process",
        "database", "index", "query", "cache", "load balancer"
    ]
    
    for keyword in technical_keywords:
        if keyword in answer_lower:
            score += 0.1
    
    # Depth indicators
    depth_keywords = [
        "because", "reason", "challenge", "problem", "solution",
        "learned", "improved", "optimized", "refactored", "migrated"
    ]
    
    depth_count = sum(1 for kw in depth_keywords if kw in answer_lower)
    score += min(depth_count * 0.05, 0.2)
    
    # Question indicators (shows engagement)
    if "?" in answer:
        score += 0.05
    
    # Code/example indicators
    if any(char in answer for char in ["{", "(", "[", "=", "->"]):
        score += 0.1
    
    return min(max(score, 0.0), 1.0)


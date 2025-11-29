"""
Database models - Matches existing Neon DB schema
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .config import Base


class User(Base):
    """User model - matches existing schema with user_id as Clerk ID"""
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)  # Clerk user ID (e.g., "user_2abc123")
    email = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    interviews = relationship("Interview", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "id": self.user_id,  # For backward compatibility
            "name": None,  # Not in DB schema yet
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Interview(Base):
    """Interview model - one row per interview setup"""
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)  # References users.user_id (String)
    title = Column(String, nullable=False)
    duration_minutes = Column(Integer, default=30, nullable=False)
    job_description = Column(Text, nullable=True)  # LLM-generated summary (full details in interview_memory)
    cv_summary = Column(Text, nullable=True)  # LLM-generated summary (full details in interview_memory)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="interviews")
    sessions = relationship("InterviewSession", back_populates="interview", cascade="all, delete-orphan")
    memory = relationship("InterviewMemory", back_populates="interview", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "job_description": self.job_description,
            "cv_summary": self.cv_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InterviewSession(Base):
    """Interview session - tracks conversation turns between AI and candidate
    Each 'start interview' creates a new session_run_id, allowing multiple mock interviews
    for the same interview preparation.
    """
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False)
    session_run_id = Column(UUID(as_uuid=True), nullable=True)  # Groups sessions for one interview run
    ai_message = Column(Text, nullable=False)  # Question or response from AI
    user_message = Column(Text, nullable=False)  # Candidate's response
    feedback = Column(Text, nullable=True)  # AI evaluation of that response
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    interview = relationship("Interview", back_populates="sessions")

    def to_dict(self):
        return {
            "id": str(self.id),
            "interview_id": str(self.interview_id),
            "session_run_id": str(self.session_run_id) if self.session_run_id else None,
            "ai_message": self.ai_message,
            "user_message": self.user_message,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InterviewMemory(Base):
    """Interview Memory - stores extracted CV/JD details for personalized interviews"""
    __tablename__ = "interview_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # CV Information
    cv_summary = Column(Text, nullable=True)  # LLM-generated summary
    cv_details = Column(JSONB, nullable=True)  # Structured extraction (skills, experience, projects, etc.)
    
    # JD Information
    jd_summary = Column(Text, nullable=True)  # LLM-generated summary
    jd_details = Column(JSONB, nullable=True)  # Structured requirements (skills needed, experience, etc.)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    interview = relationship("Interview", back_populates="memory")

    def to_dict(self):
        return {
            "id": str(self.id),
            "interview_id": str(self.interview_id),
            "cv_summary": self.cv_summary,
            "cv_details": self.cv_details,
            "jd_summary": self.jd_summary,
            "jd_details": self.jd_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

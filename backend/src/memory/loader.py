"""
Memory Loader - Loads and formats interview memory for agent context
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from src.db.models import InterviewMemory, InterviewSession, Interview


def load_interview_memory(interview_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Load interview memory (CV/JD details) from database.
    
    Args:
        interview_id: UUID of the interview
        db: Database session
        
    Returns:
        Dictionary with CV and JD information, or None if not found
    """
    memory = db.query(InterviewMemory).filter(
        InterviewMemory.interview_id == interview_id
    ).first()
    
    if not memory:
        return None
    
    return {
        "cv_summary": memory.cv_summary,
        "cv_details": memory.cv_details,
        "jd_summary": memory.jd_summary,
        "jd_details": memory.jd_details,
    }


def extract_candidate_name(memory: Dict[str, Any]) -> str:
    """
    Extract candidate name from CV details.
    
    Args:
        memory: Memory dictionary from load_interview_memory
        
    Returns:
        Candidate name or "there" as fallback
    """
    if not memory or not memory.get("cv_details"):
        return "there"
    
    cv_details = memory["cv_details"]
    if isinstance(cv_details, dict) and cv_details.get("name"):
        return cv_details["name"]
    
    return "there"


def get_relevant_cv_excerpts(memory: Dict[str, Any], current_topic: Optional[str] = None) -> str:
    """
    Get only relevant CV excerpts instead of full details.
    For first message, return summary. For follow-ups, return relevant skills.
    
    Args:
        memory: Memory dictionary
        current_topic: Current topic being discussed (optional)
        
    Returns:
        Relevant CV information string
    """
    if not memory:
        return "No CV information available."
    
    # For first message or if no topic, return summary
    if not current_topic:
        if memory.get("cv_summary"):
            return f"CANDIDATE SUMMARY:\n{memory['cv_summary']}"
        return "No CV summary available."
    
    # For follow-ups, return relevant skills/projects
    if memory.get("cv_details"):
        cv_details = memory["cv_details"]
        if isinstance(cv_details, dict):
            relevant = []
            if cv_details.get("skills"):
                skills = cv_details["skills"]
                if isinstance(skills, dict):
                    all_skills = []
                    for category, skill_list in skills.items():
                        if skill_list:
                            all_skills.extend(skill_list)
                    if all_skills:
                        relevant.append(f"Skills: {', '.join(all_skills[:10])}")  # Limit to 10
            if cv_details.get("total_experience_years"):
                relevant.append(f"Experience: {cv_details['total_experience_years']} years")
            if relevant:
                return "\n".join(relevant)
    
    return memory.get("cv_summary", "No CV details available.")


def get_relevant_jd_excerpts(memory: Dict[str, Any], current_topic: Optional[str] = None) -> str:
    """
    Get only relevant JD excerpts instead of full details.
    
    Args:
        memory: Memory dictionary
        current_topic: Current topic being discussed (optional)
        
    Returns:
        Relevant JD information string
    """
    if not memory:
        return "No JD information available."
    
    # For first message, return summary
    if not current_topic:
        if memory.get("jd_summary"):
            return f"JOB REQUIREMENTS SUMMARY:\n{memory['jd_summary']}"
        return "No JD summary available."
    
    # For follow-ups, return key requirements
    if memory.get("jd_details"):
        jd_details = memory["jd_details"]
        if isinstance(jd_details, dict):
            relevant = []
            if jd_details.get("must_have_skills"):
                relevant.append(f"Required Skills: {', '.join(jd_details['must_have_skills'][:5])}")
            if jd_details.get("role"):
                relevant.append(f"Role: {jd_details['role']}")
            if relevant:
                return "\n".join(relevant)
    
    return memory.get("jd_summary", "No JD details available.")


def format_memory_for_prompt(memory: Dict[str, Any], is_first_message: bool = False, current_topic: Optional[str] = None) -> str:
    """
    Format interview memory into a readable prompt string.
    Uses smart context loading - full context for first message, excerpts for follow-ups.
    
    Args:
        memory: Memory dictionary from load_interview_memory
        is_first_message: Whether this is the first message (opening question)
        current_topic: Current topic being discussed (for follow-ups)
        
    Returns:
        Formatted string for use in LLM prompts
    """
    if not memory:
        return "No interview memory available."
    
    if is_first_message:
        # First message: Use summaries for context
        formatted = []
        if memory.get("cv_summary"):
            formatted.append(f"CANDIDATE CV SUMMARY:\n{memory['cv_summary']}")
        if memory.get("jd_summary"):
            formatted.append(f"\nJOB DESCRIPTION SUMMARY:\n{memory['jd_summary']}")
        return "\n".join(formatted) if formatted else "No information available."
    else:
        # Follow-ups: Use relevant excerpts
        cv_excerpt = get_relevant_cv_excerpts(memory, current_topic)
        jd_excerpt = get_relevant_jd_excerpts(memory, current_topic)
        return f"{cv_excerpt}\n\n{jd_excerpt}"


def get_recent_sessions(interview_id: str, limit: int, db: Session, session_run_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get recent conversation sessions (Q&As) for context.
    If session_run_id is provided, only returns sessions from that run.
    
    Args:
        interview_id: UUID of the interview
        limit: Maximum number of recent sessions to return
        db: Database session
        session_run_id: Optional UUID to filter by session run
        
    Returns:
        List of session dictionaries with ai_message, user_message, feedback
    """
    query = db.query(InterviewSession).filter(
        InterviewSession.interview_id == interview_id
    )
    
    # Filter by session_run_id if provided
    if session_run_id:
        try:
            import uuid
            run_uuid = uuid.UUID(session_run_id)
            query = query.filter(InterviewSession.session_run_id == run_uuid)
        except ValueError:
            pass  # Invalid UUID, ignore filter
    
    sessions = query.order_by(InterviewSession.created_at.desc()).limit(limit).all()
    
    # Reverse to get chronological order
    sessions.reverse()
    
    return [
        {
            "ai_message": session.ai_message,
            "user_message": session.user_message,
            "feedback": session.feedback,
            "created_at": session.created_at.isoformat() if session.created_at else None,
        }
        for session in sessions
    ]


def format_recent_conversation(sessions: List[Dict[str, Any]], max_turns: int = 3) -> str:
    """
    Format recent conversation sessions into a readable string.
    Limits to last N turns to reduce prompt size.
    
    Args:
        sessions: List of session dictionaries
        max_turns: Maximum number of turns to include
        
    Returns:
        Formatted conversation history string
    """
    if not sessions:
        return "No previous conversation."
    
    # Only use last N turns
    recent_sessions = sessions[-max_turns:] if len(sessions) > max_turns else sessions
    
    formatted = []
    for i, session in enumerate(recent_sessions, 1):
        formatted.append(f"\n--- Turn {i} ---")
        formatted.append(f"AI: {session['ai_message']}")
        formatted.append(f"Candidate: {session['user_message']}")
        if session.get("feedback"):
            formatted.append(f"Feedback: {session['feedback']}")
    
    return "\n".join(formatted)


def get_interview_stage(question_count: int, duration_minutes: int) -> str:
    """
    Determine interview stage based on question count and duration.
    
    Args:
        question_count: Number of questions asked so far
        duration_minutes: Total interview duration
        
    Returns:
        Stage: "intro", "technical", "behavioral", or "closing"
    """
    # Estimate questions per minute (roughly 1 question per 2-3 minutes)
    total_questions = duration_minutes // 2
    
    if question_count == 0:
        return "intro"
    elif question_count <= total_questions * 0.3:
        return "intro"
    elif question_count <= total_questions * 0.7:
        return "technical"
    elif question_count <= total_questions * 0.9:
        return "behavioral"
    else:
        return "closing"


def extract_cv_highlights(cv_details: Dict[str, Any]) -> List[str]:
    """
    Extract key highlights from CV details for state machine.
    
    Args:
        cv_details: CV details dictionary
        
    Returns:
        List of key highlights (skills, projects, etc.)
    """
    highlights = []
    if not cv_details or not isinstance(cv_details, dict):
        return highlights
    
    # Extract skills
    skills = cv_details.get("skills")
    if skills:
        if isinstance(skills, dict):
            for category, skill_list in skills.items():
                if skill_list and isinstance(skill_list, list):
                    highlights.extend(skill_list[:3])  # Top 3 per category
        elif isinstance(skills, list):
            highlights.extend(skills[:5])
    
    # Extract projects
    projects = cv_details.get("projects")
    if projects and isinstance(projects, list):
        for project in projects[:2]:  # Top 2 projects
            if isinstance(project, dict) and project.get("name"):
                highlights.append(f"Project: {project['name']}")
            elif isinstance(project, str):
                highlights.append(f"Project: {project}")
    
    return highlights[:10]  # Limit to 10 highlights


def extract_jd_requirements(jd_details: Dict[str, Any]) -> List[str]:
    """
    Extract key requirements from JD details for state machine.
    
    Args:
        jd_details: JD details dictionary
        
    Returns:
        List of key requirements
    """
    requirements = []
    if not jd_details or not isinstance(jd_details, dict):
        return requirements
    
    # Safely extract must_have_skills
    must_have_skills = jd_details.get("must_have_skills")
    if must_have_skills:
        if isinstance(must_have_skills, list):
            requirements.extend(must_have_skills[:5])
        elif isinstance(must_have_skills, str):
            requirements.append(must_have_skills)
    
    # Safely extract role
    role = jd_details.get("role")
    if role:
        requirements.append(f"Role: {role}")
    
    # Extract other useful fields
    if jd_details.get("required_experience_years"):
        requirements.append(f"Experience: {jd_details['required_experience_years']} years")
    
    return requirements[:8]  # Limit to 8 requirements


"""
Planner Agent - Designs interview structure and question types
"""
from typing import Dict, Any, List
from .base import BaseAgent


class PlannerAgent(BaseAgent):
    """
    Planner Agent designs the interview structure:
    - Chooses question types (behavioral, technical, coding, system design)
    - Plans question sequence
    - Adapts based on candidate responses
    """
    
    def __init__(self):
        super().__init__(model_name="gemini-2.5-flash", temperature=0.7)
    
    def plan_interview_structure(
        self,
        cv_details: Dict[str, Any],
        jd_details: Dict[str, Any],
        duration_minutes: int
    ) -> Dict[str, Any]:
        """
        Plan the overall interview structure.
        
        Args:
            cv_details: Candidate CV details
            jd_details: Job description details
            duration_minutes: Interview duration
            
        Returns:
            Interview plan with question types and sequence
        """
        system_instruction = """You are an interview planner. Design a structured interview plan based on:
1. Candidate's experience and skills
2. Job requirements
3. Interview duration

Create a balanced mix of:
- Behavioral questions (experience, past projects)
- Technical questions (skills, knowledge)
- Problem-solving questions (if time permits)
- System design questions (for senior roles)"""
        
        prompt = f"""Plan an interview structure for:
- Duration: {duration_minutes} minutes
- Candidate Skills: {cv_details.get('skills', {})}
- Job Requirements: {jd_details.get('must_have_skills', [])}

Generate a JSON structure with:
{{
  "question_types": ["behavioral", "technical", "problem_solving"],
  "estimated_time_per_question": 5,
  "total_questions": {duration_minutes // 5},
  "focus_areas": ["list of key areas to cover"]
}}"""
        
        response = self.generate_response(prompt, system_instruction)
        
        # For now, return a simple structure
        # In production, parse JSON response
        return {
            "question_types": ["behavioral", "technical"],
            "estimated_time_per_question": 5,
            "total_questions": duration_minutes // 5,
            "focus_areas": jd_details.get("must_have_skills", [])[:5]
        }
    
    def suggest_question_type(
        self,
        conversation_history: List[Dict[str, Any]],
        interview_progress: float
    ) -> str:
        """
        Suggest the next question type based on interview progress.
        
        Args:
            conversation_history: Recent conversation turns
            interview_progress: Progress percentage (0.0-1.0)
            
        Returns:
            Suggested question type
        """
        if interview_progress < 0.3:
            return "behavioral"
        elif interview_progress < 0.7:
            return "technical"
        else:
            return "problem_solving"


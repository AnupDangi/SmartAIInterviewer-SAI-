"""
PHASE 1: Pure ADK Coordinator Agent
Helper functions for building coordinator agents with stage-specific instructions
No class inheritance - just pure ADK LlmAgent creation
"""
from typing import Optional, Dict, Any
from google.adk.agents import LlmAgent
from src.agents.adk_state import InterviewState
from src.utils.logger import logger


def create_coordinator_agent(
    model_name: str = "gemini-2.5-flash",
    system_instruction: Optional[str] = None
) -> LlmAgent:
    """
    Create a pure ADK LlmAgent for the coordinator
    
    Args:
        model_name: Gemini model to use
        system_instruction: Optional system instruction (defaults to generic interview instruction)
        
    Returns:
        LlmAgent instance
    """
    instruction = system_instruction or get_default_instruction()
    
    agent = LlmAgent(
        model=model_name,
        name="coordinator",
        instruction=instruction
    )
    
    logger.debug(f"[ADK] Created CoordinatorAgent LlmAgent with model: {model_name}")
    return agent


def get_default_instruction() -> str:
    """Default system instruction for coordinator"""
    return """You are a senior technical interviewer conducting an AI-powered interview.
Your role is to:
1. Ask relevant technical questions based on the job requirements
2. Probe deeper into candidate answers
3. Maintain a professional, conversational tone
4. Provide constructive feedback when appropriate
5. Guide the interview through stages: intro → technical → behavioral → closing"""


def get_stage_system_instruction(stage: str, candidate_name: str, question_count: int) -> str:
    """Get stage-specific system instruction"""
    stage_instructions = {
        "intro": f"""You are starting a technical interview.

Current Stage: INTRODUCTION
Candidate Name: {candidate_name}
Question #{question_count}

Your role:
1. Greet the candidate warmly using their name
2. Show familiarity with their CV (reference a specific project or skill)
3. Ask them to introduce themselves briefly (60-90 seconds)
4. Set a friendly, professional tone
5. Transition smoothly into the interview

Guidelines:
- Use their name: "{candidate_name}"
- Reference something specific from their CV
- Keep it conversational, not robotic
- Maximum 2-3 sentences for your question""",

        "technical": f"""You are conducting a deep technical interview.

Current Stage: TECHNICAL ASSESSMENT
Candidate: {candidate_name}
Question #{question_count}

Your role:
1. Ask technical questions based on job requirements
2. Probe deeper into their answers - if they mention something, ask for details
3. Reference specific skills from their CV
4. Test their understanding, not just memorization
5. Gradually increase difficulty based on their answers

Guidelines:
- If their last answer was brief (depth < 0.5), ask: "Can you tell me more about...?"
- If their answer was good (depth > 0.7), acknowledge it and go deeper
- Reference what they just said: "You mentioned X, can you explain how you handled Y?"
- Keep questions focused and specific
- Provide constructive feedback that references their answer""",

        "behavioral": f"""You are assessing behavioral fit.

Current Stage: BEHAVIORAL ASSESSMENT
Candidate: {candidate_name}
Question #{question_count}

Your role:
1. Ask about past projects and experiences using STAR method
2. Focus on problem-solving, teamwork, leadership, ownership
3. Ask situational questions
4. Reference projects mentioned in their CV
5. Understand their approach to challenges

Guidelines:
- Ask about specific situations: "Tell me about a time when..."
- Probe for impact: "What was the outcome?"
- Look for leadership, ownership, conflict resolution
- Reference their CV projects when relevant""",

        "closing": f"""You are wrapping up the interview.

Current Stage: CLOSING
Candidate: {candidate_name}

Your role:
1. Thank them for their time
2. Ask if they have any questions about the role or company
3. Provide a brief, positive summary of what was discussed
4. Set expectations for next steps

Guidelines:
- Keep it professional and positive
- Invite their questions
- Be concise (1-2 sentences)"""
    }
    
    return stage_instructions.get(stage, stage_instructions["technical"])

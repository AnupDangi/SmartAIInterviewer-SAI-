"""
PHASE 1: Test Script
Run this to verify Phase 1 ADK architecture works
"""
import asyncio
import os
from dotenv import load_dotenv

# Import Phase 1 components
from src.agents.adk_runner import create_session, run_agent, get_session_state
from src.agents.adk_state import InterviewState

load_dotenv()


async def test_phase1():
    """Test Phase 1 ADK implementation"""
    print("=" * 60)
    print("PHASE 1 ADK TEST")
    print("=" * 60)
    
    # Test 1: Session Creation
    print("\n1. Testing session creation...")
    try:
        session = await create_session(
            user_id="test_user",
            session_id="test_session_001",
            initial_state={
                "stage": "intro",
                "question_count": 0,
                "candidate_name": "Test Candidate"
            }
        )
        print(f"✅ Session created: {session.id if hasattr(session, 'id') else 'OK'}")
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return
    
    # Test 2: Get Session State
    print("\n2. Testing session state retrieval...")
    try:
        state = await get_session_state("test_user", "test_session_001")
        print(f"✅ Session state retrieved: {state}")
    except Exception as e:
        print(f"❌ State retrieval failed: {e}")
        return
    
    # Test 3: Run Agent (Opening Question)
    print("\n3. Testing agent run (opening question)...")
    try:
        opening_prompt = """Start the interview. 
        Greet the candidate and ask them to introduce themselves briefly.
        Keep it friendly and professional (2-3 sentences max)."""
        
        response = await run_agent(
            user_id="test_user",
            session_id="test_session_001",
            user_message=opening_prompt,
            state_delta={"question_count": 1}
        )
        print(f"✅ Agent response received ({len(response)} chars)")
        print(f"   Response: {response[:200]}...")
    except Exception as e:
        print(f"❌ Agent run failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 4: Run Agent (Follow-up)
    print("\n4. Testing agent run (follow-up question)...")
    try:
        user_answer = "Hi, I'm a software engineer with 5 years of experience in Python and machine learning."
        
        followup_prompt = f"""The candidate answered: "{user_answer}"

Generate a follow-up technical question about Python. 
Ask them to explain a concept or solve a problem.
Keep it conversational and build on what they said."""
        
        response = await run_agent(
            user_id="test_user",
            session_id="test_session_001",
            user_message=followup_prompt,
            state_delta={"question_count": 2, "stage": "technical"}
        )
        print(f"✅ Follow-up response received ({len(response)} chars)")
        print(f"   Response: {response[:200]}...")
    except Exception as e:
        print(f"❌ Follow-up failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 5: Verify State Persistence
    print("\n5. Testing state persistence...")
    try:
        state = await get_session_state("test_user", "test_session_001")
        print(f"✅ Final state: {state}")
    except Exception as e:
        print(f"❌ State check failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ PHASE 1 TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY not found in environment")
        print("   Set it in .env file or export GEMINI_API_KEY=your_key")
        exit(1)
    
    print(f"Using API key: {api_key[:10]}...")
    asyncio.run(test_phase1())


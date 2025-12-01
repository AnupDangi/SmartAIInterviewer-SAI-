"""
FastAPI Backend for Smart AI Interviewer
"""
from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File as FastAPIFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import os
import jwt
import aiofiles
import uvicorn
import fitz  # PyMuPDF
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

from src.db.config import get_db, init_db
from src.db.models import User, Interview, InterviewSession, InterviewMemory
from src.memory.extractor import (
    extract_text_from_pdf,
    extract_text_from_txt,
    extract_cv_details,
    extract_jd_details,
    generate_cv_summary,
    generate_jd_summary
)
from src.agents import CoordinatorAgent
from src.memory.loader import get_recent_sessions

load_dotenv()

app = FastAPI(title="Smart AI Interviewer API", version="1.0.0")

# CORS middleware - Fixed to handle OPTIONS requests properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",  # Added for Vite dev server on port 8080
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Clerk configuration
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY")

# Create uploads directory if it doesn't exist
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)
CV_DIR = UPLOADS_DIR / "cv"
JD_DIR = UPLOADS_DIR / "jd"
CV_DIR.mkdir(exist_ok=True)
JD_DIR.mkdir(exist_ok=True)


# Text extraction and LLM processing functions are in src.memory.extractor


# AI processing functions are now in src.memory.extractor


def verify_clerk_token(request: Request, authorization: Optional[str] = Header(None)):
    """
    Verify Clerk JWT token and extract user information
    Returns: dict with 'user_id' and 'email'
    Skips verification for OPTIONS requests (CORS preflight)
    """
    # Skip auth for OPTIONS requests (CORS preflight) - return None to allow CORS middleware to handle it
    if request.method == "OPTIONS":
        return None
    
    # Allow requests without authorization for development (will fail in production)
    if not authorization:
        # For development, allow but return a default user
        # In production, this should raise HTTPException
        return {
            "user_id": "dev_user",
            "email": "dev@example.com",
            "name": None
        }
    
    # Extract token from "Bearer <token>"
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    try:
        # Decode JWT without verification for now (development mode)
        # In production, verify with Clerk's public key
        decoded = jwt.decode(
            token,
            options={"verify_signature": False}  # Skip verification for now
        )
        
        # Extract user info from Clerk JWT
        # Clerk JWT structure: sub = user_id, email in claims
        user_id = decoded.get("sub") or decoded.get("user_id")
        email = decoded.get("email") or decoded.get("primary_email_address")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user_id")
        
        return {
            "user_id": user_id,
            "email": email or f"{user_id}@clerk.user",
            "name": decoded.get("name") or decoded.get("first_name")
        }
    except jwt.DecodeError:
        # If JWT decode fails, treat token as user_id (fallback for development)
        # This allows testing without proper JWT tokens
        return {
            "user_id": token,
            "email": f"{token}@clerk.user",
            "name": None
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


@app.middleware("http")
async def handle_cors_and_options(request: Request, call_next):
    """Handle OPTIONS requests and ensure CORS headers on all responses"""
    # Handle OPTIONS preflight
    if request.method == "OPTIONS":
        response = Response()
        origin = request.headers.get("origin")
        # allowed_origins = [
        #     "http://localhost:5173",
        #     "http://localhost:3000",
        #     "http://localhost:8080",
        #     "http://127.0.0.1:5173",
        #     "http://127.0.0.1:8080",
        # ]
        allowed_origins = ["https://smart-ai-interviewer-sai.vercel.app/", "https://smart-ai-interviewer-sai.vercel.app"]
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "3600"
        return response
    
    # Process request
    try:
        response = await call_next(request)
    except Exception as e:
        # Ensure CORS headers even on errors
        import traceback
        error_detail = str(e)
        response = Response(
            content=f'{{"detail": "{error_detail}"}}',
            status_code=500,
            media_type="application/json"
        )
    
    # Add CORS headers to all responses (including errors)
    origin = request.headers.get("origin")
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ]
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("Database initialized")
    print(f"Uploads directory: {UPLOADS_DIR.absolute()}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Smart AI Interviewer API", "status": "healthy"}


# Pydantic models for request/response
class CreateInterviewRequest(BaseModel):
    title: str
    duration_minutes: int = 30
    # job_description and cv_summary will be processed by AI after upload


class CreateInterviewSessionRequest(BaseModel):
    ai_message: str
    user_message: str


class SendMessageRequest(BaseModel):
    user_message: str
    session_run_id: Optional[str] = None  # Optional - if not provided, uses most recent run


class ProcessJDTextRequest(BaseModel):
    text: str


class UpdateInterviewRequest(BaseModel):
    title: Optional[str] = None
    duration_minutes: Optional[int] = None


class UpdateCVRequest(BaseModel):
    # For re-uploading CV, use the upload endpoint
    pass


class UpdateJDRequest(BaseModel):
    # For re-uploading JD, use the upload endpoint
    pass


@app.get("/api/users/me")
async def get_current_user(
    request: Request,
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    """
    Get or create current user from Clerk token
    This endpoint is called on dashboard load to ensure user exists in DB
    """
    # Handle OPTIONS preflight
    if request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    
    clerk_user_id = user_info["user_id"]
    email = user_info["email"]
    
    # Find user by Clerk user_id
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    
    if not user:
        # Create new user with Clerk user_id
        user = User(
            user_id=clerk_user_id,
            email=email
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created new user: {clerk_user_id} ({email})")
    else:
        # Update email if changed
        if user.email != email:
            user.email = email
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
    
    return user.to_dict()


@app.post("/api/interviews/create")
async def create_interview(
    request: Request,
    data: CreateInterviewRequest,
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    """
    Create a new interview with title, duration, and optional job description
    """
    # Handle OPTIONS preflight
    if request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    
    clerk_user_id = user_info["user_id"]
    
    # Get or create user
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        user = User(
            user_id=clerk_user_id,
            email=user_info["email"]
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create interview - only store title and duration
    # job_description and cv_summary will be processed by AI after upload
    interview = Interview(
        user_id=user.user_id,
        title=data.title,
        duration_minutes=data.duration_minutes,
        job_description=None,  # Will be processed by AI after upload
        cv_summary=None  # Will be processed by AI after upload
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    return interview.to_dict()


@app.put("/api/interviews/{interview_id}")
async def update_interview(
    request: Request,
    interview_id: str,
    data: UpdateInterviewRequest,
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    """
    Update interview title and/or duration
    """
    # Handle OPTIONS preflight
    if request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    
    clerk_user_id = user_info["user_id"]
    
    # Verify interview belongs to user
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user.user_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Update fields if provided
    if data.title is not None:
        interview.title = data.title
    if data.duration_minutes is not None:
        interview.duration_minutes = data.duration_minutes
    
    db.commit()
    db.refresh(interview)
    
    return interview.to_dict()


@app.delete("/api/interviews/{interview_id}")
async def delete_interview(
    request: Request,
    interview_id: str,
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    """
    Delete an interview and all associated data (sessions, memory, files)
    """
    # Handle OPTIONS preflight
    if request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    
    clerk_user_id = user_info["user_id"]
    
    # Verify interview belongs to user
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Convert interview_id to UUID if it's a string
    try:
        import uuid as uuid_lib
        interview_uuid = uuid_lib.UUID(interview_id) if isinstance(interview_id, str) else interview_id
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid interview ID format")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_uuid,
        Interview.user_id == user.user_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Delete associated memory first (if exists)
    try:
        memory = db.query(InterviewMemory).filter(InterviewMemory.interview_id == interview_uuid).first()
        if memory:
            db.delete(memory)
            db.flush()  # Flush but don't commit yet
    except Exception as e:
        print(f"Error deleting memory: {e}")
        # Continue anyway
    
    # Delete associated files from disk
    try:
        cv_files = list(CV_DIR.glob(f"{interview_id}_*"))
        jd_files = list(JD_DIR.glob(f"{interview_id}_*"))
        for file_path in cv_files + jd_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
    except Exception as e:
        print(f"Error listing files: {e}")
    
    # Delete interview (cascade will delete sessions)
    try:
        db.delete(interview)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error deleting interview: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete interview: {str(e)}")
    
    return {
        "message": "Interview deleted successfully",
        "interview_id": interview_id
    }


@app.post("/api/interviews/{interview_id}/upload-cv")
async def upload_cv(
    request: Request,
    interview_id: str,
    file: UploadFile = FastAPIFile(...),
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    # Handle OPTIONS preflight
    if request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    
    """
    Upload or update CV PDF for an interview
    If CV already exists, it will be replaced
    """
    clerk_user_id = user_info["user_id"]
    
    # Verify interview belongs to user
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user.user_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Delete old CV files if they exist
    try:
        old_cv_files = list(CV_DIR.glob(f"{interview_id}_*"))
        for old_file in old_cv_files:
            try:
                if old_file.exists():
                    old_file.unlink()
            except Exception as e:
                print(f"Error deleting old CV file {old_file}: {e}")
    except Exception as e:
        print(f"Error listing old CV files: {e}")
    
    # Save new file
    file_path = CV_DIR / f"{interview_id}_{file.filename}"
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Extract text from PDF
    cv_text = extract_text_from_pdf(str(file_path))
    
    if not cv_text:
        raise HTTPException(status_code=400, detail="Failed to extract text from PDF")
    
    print(f"Processing CV for interview {interview_id}...")
    
    # Extract structured details using LLM (synchronous functions)
    cv_summary = generate_cv_summary(cv_text)
    cv_details = extract_cv_details(cv_text)
    
    # Get or create interview memory
    memory = db.query(InterviewMemory).filter(InterviewMemory.interview_id == interview.id).first()
    if not memory:
        memory = InterviewMemory(interview_id=interview.id)
        db.add(memory)
    
    # Update memory with CV information
    memory.cv_summary = cv_summary
    memory.cv_details = cv_details
    memory.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(memory)
    
    # Also update interview record with summary for backward compatibility
    interview.cv_summary = cv_summary
    db.commit()
    db.refresh(interview)
    
    return {
        "message": "CV uploaded and processed successfully",
        "interview_id": interview_id,
        "filename": file.filename,
        "file_saved": str(file_path),
        "text_extracted": len(cv_text) > 0,
        "summary_length": len(cv_summary) if cv_summary else 0,
        "details_extracted": cv_details is not None,
        "summary_preview": cv_summary[:200] + "..." if cv_summary and len(cv_summary) > 200 else cv_summary
    }


@app.post("/api/interviews/{interview_id}/upload-jd")
async def upload_job_description(
    request: Request,
    interview_id: str,
    file: UploadFile = FastAPIFile(...),
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    # Handle OPTIONS preflight
    if request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    
    """
    Upload Job Description PDF for an interview
    Saves file, extracts text, updates job_description field
    """
    clerk_user_id = user_info["user_id"]
    
    # Verify interview belongs to user
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user.user_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save file
    file_path = JD_DIR / f"{interview_id}_{file.filename}"
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Extract text from PDF
    jd_text = extract_text_from_pdf(str(file_path))
    
    if not jd_text:
        raise HTTPException(status_code=400, detail="Failed to extract text from PDF")
    
    print(f"Processing JD for interview {interview_id}...")
    
    # Extract structured details using LLM
    jd_summary = generate_jd_summary(jd_text)
    jd_details = extract_jd_details(jd_text)
    
    # Get or create interview memory
    memory = db.query(InterviewMemory).filter(InterviewMemory.interview_id == interview.id).first()
    if not memory:
        memory = InterviewMemory(interview_id=interview.id)
        db.add(memory)
    
    # Update memory with JD information
    memory.jd_summary = jd_summary
    memory.jd_details = jd_details
    memory.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(memory)
    
    # Also update interview record with summary for backward compatibility
    interview.job_description = jd_summary  # Store summary instead of full text
    db.commit()
    db.refresh(interview)
    
    return {
        "message": "Job Description uploaded and processed successfully",
        "interview_id": interview_id,
        "filename": file.filename,
        "file_saved": str(file_path),
        "text_extracted": len(jd_text) > 0,
        "summary_length": len(jd_summary) if jd_summary else 0,
        "details_extracted": jd_details is not None,
        "preview": jd_summary[:200] + "..." if jd_summary and len(jd_summary) > 200 else jd_summary
    }


@app.post("/api/interviews/{interview_id}/process-jd-text")
async def process_jd_text(
    request: Request,
    interview_id: str,
    data: ProcessJDTextRequest,
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    """
    Process job description text (from textarea) with AI and save as file
    """
    # Handle OPTIONS preflight
    if request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    
    clerk_user_id = user_info["user_id"]
    
    # Verify interview belongs to user
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user.user_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if not data.text or not data.text.strip():
        raise HTTPException(status_code=400, detail="Job description text cannot be empty")
    
    # Delete old JD text files if they exist
    try:
        old_jd_files = list(JD_DIR.glob(f"{interview_id}_*"))
        for old_file in old_jd_files:
            try:
                if old_file.exists():
                    old_file.unlink()
            except Exception as e:
                print(f"Error deleting old JD file {old_file}: {e}")
    except Exception as e:
        print(f"Error listing old JD files: {e}")
    
    # Save text as file
    file_path = JD_DIR / f"{interview_id}_job_description.txt"
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
        await f.write(data.text)
    
    print(f"Processing JD text for interview {interview_id}...")
    
    # Extract structured details using LLM
    jd_summary = generate_jd_summary(data.text)
    jd_details = extract_jd_details(data.text)
    
    # Get or create interview memory
    memory = db.query(InterviewMemory).filter(InterviewMemory.interview_id == interview.id).first()
    if not memory:
        memory = InterviewMemory(interview_id=interview.id)
        db.add(memory)
    
    # Update memory with JD information
    memory.jd_summary = jd_summary
    memory.jd_details = jd_details
    memory.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(memory)
    
    # Also update interview record with summary for backward compatibility
    interview.job_description = jd_summary
    db.commit()
    db.refresh(interview)
    
    return {
        "message": "Job Description text saved and processed successfully",
        "interview_id": interview_id,
        "file_saved": str(file_path),
        "summary_length": len(jd_summary) if jd_summary else 0,
        "details_extracted": jd_details is not None,
        "preview": jd_summary[:200] + "..." if jd_summary and len(jd_summary) > 200 else jd_summary
    }


@app.get("/api/interviews")
async def get_user_interviews(
    request: Request,
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    # Handle OPTIONS preflight
    if request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    """
    Get all interviews for the current user
    """
    clerk_user_id = user_info["user_id"]
    
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        return []
    
    interviews = db.query(Interview).filter(
        Interview.user_id == user.user_id  # Use user_id (String)
    ).order_by(Interview.created_at.desc()).all()
    
    return [interview.to_dict() for interview in interviews]


@app.get("/api/interviews/{interview_id}")
async def get_interview(
    request: Request,
    interview_id: str,
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    # Handle OPTIONS preflight
    if request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    """
    Get a specific interview by ID
    """
    clerk_user_id = user_info["user_id"]
    
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user.user_id  # Use user_id (String)
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    return interview.to_dict()


@app.post("/api/interviews/{interview_id}/sessions")
async def create_interview_session(
    http_request: Request,
    interview_id: str,
    request: CreateInterviewSessionRequest,
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    # Handle OPTIONS preflight
    if http_request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    """
    Create a new interview session (conversation turn)
    """
    clerk_user_id = user_info["user_id"]
    
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user.user_id  # Use user_id (String)
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    session = InterviewSession(
        interview_id=interview.id,
        ai_message=request.ai_message,
        user_message=request.user_message,
        feedback=None  # Will be filled by AI evaluation
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session.to_dict()


@app.get("/api/interviews/{interview_id}/sessions")
async def get_interview_sessions(
    request: Request,
    interview_id: str,
    session_run_id: Optional[str] = None,  # Optional query parameter: filter by session run
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    # Handle OPTIONS preflight
    if request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    """
    Get all sessions for an interview.
    If session_run_id is provided, only returns sessions from that run.
    Otherwise, returns all sessions (for viewing history of all mock interviews).
    """
    clerk_user_id = user_info["user_id"]
    
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user.user_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Build query
    query = db.query(InterviewSession).filter(
        InterviewSession.interview_id == interview.id
    )
    
    # Filter by session_run_id if provided
    if session_run_id:
        try:
            import uuid
            run_uuid = uuid.UUID(session_run_id)
            query = query.filter(InterviewSession.session_run_id == run_uuid)
            print(f"[DEBUG] Filtering sessions by session_run_id: {session_run_id}")
        except ValueError:
            # Invalid UUID, ignore filter
            pass
    
    sessions = query.order_by(InterviewSession.created_at.asc()).all()
    
    print(f"[DEBUG] Returning {len(sessions)} sessions for interview {interview_id}")
    
    return [session.to_dict() for session in sessions]


@app.post("/api/interviews/{interview_id}/start")
async def start_interview(
    http_request: Request,
    interview_id: str,
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    """
    Start an interview session - generates opening question using Coordinator Agent
    Creates a new session_run_id for this interview run (allows multiple mock interviews)
    """
    # Handle OPTIONS preflight
    if http_request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    
    clerk_user_id = user_info["user_id"]
    
    # Verify interview belongs to user
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user.user_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Create a new session_run_id for this interview run
    import uuid
    session_run_id = uuid.uuid4()
    
    # Initialize Coordinator Agent
    coordinator = CoordinatorAgent()
    
    # Generate opening question
    try:
        print(f"[DEBUG] Starting interview {interview_id}, session_run_id: {session_run_id}")
        result = await coordinator.generate_opening_question(
            interview_id=interview_id,
            interview_title=interview.title,
            duration_minutes=interview.duration_minutes,
            db=db,
            session_run_id=str(session_run_id),  # Pass session_run_id for ADK Session
            user_id=clerk_user_id  # Pass user_id for ADK Session
        )
        
        opening_question = result["question"]
        print(f"[DEBUG] Generated opening question: {opening_question[:100]}...")
        
        # Save the opening question as a placeholder session
        # When the first user message arrives, we'll update this session
        opening_session = InterviewSession(
            interview_id=interview.id,
            session_run_id=session_run_id,
            ai_message=opening_question,
            user_message="[INTERVIEW_STARTED]",  # Placeholder - will be updated on first message
            feedback=None
        )
        db.add(opening_session)
        db.commit()
        db.refresh(opening_session)
        print(f"[DEBUG] Saved opening session: {opening_session.id} for new session_run_id: {session_run_id}")
        
        # Get interview memory for context
        memory = db.query(InterviewMemory).filter(
            InterviewMemory.interview_id == interview.id
        ).first()
        
        return {
            "interview_id": interview_id,
            "session_run_id": str(session_run_id),
            "opening_question": opening_question,
            "interview_title": interview.title,
            "duration_minutes": interview.duration_minutes,
            "cv_summary": memory.cv_summary if memory else None,
            "jd_summary": memory.jd_summary if memory else None,
            "status": "started"
        }
    except Exception as e:
        print(f"[ERROR] Error starting interview: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")


@app.post("/api/interviews/{interview_id}/messages")
async def send_message(
    http_request: Request,
    interview_id: str,
    request: SendMessageRequest,
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    """
    Send a message in the interview - AI generates response using Coordinator Agent
    """
    # Handle OPTIONS preflight
    if http_request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    
    clerk_user_id = user_info["user_id"]
    
    # Verify interview belongs to user
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user.user_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if not request.user_message or not request.user_message.strip():
        raise HTTPException(status_code=400, detail="User message cannot be empty")
    
    # Initialize coordinator agent
    coordinator = CoordinatorAgent()
    
    try:
        # Get or create session_run_id
        import uuid
        session_run_id = None
        if request.session_run_id:
            try:
                session_run_id = uuid.UUID(request.session_run_id)
            except ValueError:
                session_run_id = None
        
        # If no session_run_id provided, get the most recent one for this interview
        if not session_run_id:
            latest_session = db.query(InterviewSession).filter(
                InterviewSession.interview_id == interview.id
            ).order_by(InterviewSession.created_at.desc()).first()
            
            if latest_session and latest_session.session_run_id:
                session_run_id = latest_session.session_run_id
                print(f"[DEBUG] Using existing session_run_id: {session_run_id}")
            else:
                # Create new session run if none exists
                session_run_id = uuid.uuid4()
                print(f"[DEBUG] Created new session_run_id: {session_run_id}")
        
        # Get recent conversation history for THIS session run only
        recent_sessions = db.query(InterviewSession).filter(
            InterviewSession.interview_id == interview.id,
            InterviewSession.session_run_id == session_run_id
        ).order_by(InterviewSession.created_at.desc()).limit(5).all()
        
        # Reverse to get chronological order
        recent_sessions.reverse()
        
        # Convert to dict format
        recent_sessions_dict = [
            {
                "ai_message": s.ai_message,
                "user_message": s.user_message,
                "feedback": s.feedback,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in recent_sessions
        ]
        
        print(f"[DEBUG] Found {len(recent_sessions_dict)} recent sessions for run {session_run_id}")
        
        # Generate AI response and feedback (ONLY ONE LLM CALL - FAST!)
        result = await coordinator.generate_follow_up_question(
            interview_id=interview_id,
            interview_title=interview.title,
            user_message=request.user_message,
            db=db,
            session_run_id=str(session_run_id),  # Pass session_run_id for ADK Session
            user_id=clerk_user_id,  # Pass user_id for ADK Session
            recent_sessions=recent_sessions_dict
        )
        
        ai_message = result["question"]
        feedback = result.get("feedback")
        
        print(f"[DEBUG] Generated AI response: {ai_message[:100]}...")
        
        # NOTE: MemoryAgent removed from critical path for speed
        # Can be called async/background if needed later
        
        # Check if this is the first message in this session run
        existing_sessions = db.query(InterviewSession).filter(
            InterviewSession.interview_id == interview.id,
            InterviewSession.session_run_id == session_run_id
        ).count()
        
        # If this is the first message, we need to get the opening question from the start_interview call
        # It should be in a session with user_message="[INTERVIEW_STARTED]"
        opening_session = None
        if existing_sessions == 0:
            # Look for the opening question session
            opening_session = db.query(InterviewSession).filter(
                InterviewSession.interview_id == interview.id,
                InterviewSession.session_run_id == session_run_id,
                InterviewSession.user_message == "[INTERVIEW_STARTED]"
            ).first()
            
            if opening_session:
                # Update the opening session with the actual user message and AI response
                opening_session.user_message = request.user_message
                opening_session.ai_message = ai_message
                opening_session.feedback = feedback
                db.commit()
                db.refresh(opening_session)
                print(f"[DEBUG] Updated opening session: {opening_session.id}")
                
                return {
                    "session_id": str(opening_session.id),
                    "session_run_id": str(session_run_id),
                    "ai_message": ai_message,
                    "feedback": feedback,
                    "created_at": opening_session.created_at.isoformat() if opening_session.created_at else None
                }
        
        # Save session to database with session_run_id
        session = InterviewSession(
            interview_id=interview.id,
            session_run_id=session_run_id,
            ai_message=ai_message,
            user_message=request.user_message,
            feedback=feedback
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        print(f"[DEBUG] Saved session: {session.id} to run: {session_run_id}")
        
        return {
            "session_id": str(session.id),
            "session_run_id": str(session_run_id),
            "ai_message": ai_message,
            "feedback": feedback,
            "created_at": session.created_at.isoformat() if session.created_at else None
        }
    except Exception as e:
        print(f"Error sending message: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@app.get("/api/interviews/{interview_id}/memory")
async def get_interview_memory(
    request: Request,
    interview_id: str,
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    """
    Get interview memory (extracted CV/JD details) for personalized interviews
    """
    # Handle OPTIONS preflight
    if request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    
    clerk_user_id = user_info["user_id"]
    
    # Verify interview belongs to user
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user.user_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Get memory
    memory = db.query(InterviewMemory).filter(InterviewMemory.interview_id == interview.id).first()
    
    if not memory:
        return {
            "interview_id": interview_id,
            "message": "Memory not yet created. Upload CV and JD first.",
            "cv_summary": None,
            "cv_details": None,
            "jd_summary": None,
            "jd_details": None
        }
    
    return memory.to_dict()


@app.get("/api/interviews/{interview_id}/details")
async def get_interview_details(
    request: Request,
    interview_id: str,
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    """
    Get interview details including stored text and file info
    """
    # Handle OPTIONS preflight
    if request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    
    clerk_user_id = user_info["user_id"]
    
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user.user_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Check for uploaded files
    cv_files = list(CV_DIR.glob(f"{interview_id}_*"))
    jd_files = list(JD_DIR.glob(f"{interview_id}_*"))
    
    return {
        "interview": interview.to_dict(),
        "files": {
            "cv_files": [f.name for f in cv_files],
            "jd_files": [f.name for f in jd_files],
        },
        "text_status": {
            "job_description": {
                "has_text": bool(interview.job_description),
                "length": len(interview.job_description) if interview.job_description else 0,
                "preview": interview.job_description[:200] + "..." if interview.job_description and len(interview.job_description) > 200 else interview.job_description
            },
            "cv_summary": {
                "has_summary": bool(interview.cv_summary),
                "length": len(interview.cv_summary) if interview.cv_summary else 0,
                "preview": interview.cv_summary[:200] + "..." if interview.cv_summary and len(interview.cv_summary) > 200 else interview.cv_summary
            }
        }
    }


@app.post("/api/interviews/{interview_id}/end")
async def end_interview(
    http_request: Request,
    interview_id: str,
    request: SendMessageRequest,  # Reusing to get session_run_id
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    """
    End an interview session and clean up ADK resources
    """
    # Handle OPTIONS preflight
    if http_request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    
    clerk_user_id = user_info["user_id"]
    
    # Verify interview belongs to user
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user.user_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    try:
        # Get session_run_id
        import uuid
        session_run_id = None
        if request.session_run_id:
            try:
                session_run_id = uuid.UUID(request.session_run_id)
            except ValueError:
                session_run_id = None
        
        if session_run_id:
            print(f"[DEBUG] Ending interview session: {session_run_id}")
            
            # Generate session summary
            from src.agents.coordinator import CoordinatorAgent
            coordinator = CoordinatorAgent()
            summary = await coordinator.generate_session_summary(str(session_run_id), clerk_user_id)
            
            # Create a marker session to indicate this run is ended
            end_session = InterviewSession(
                interview_id=interview.id,
                session_run_id=session_run_id,
                ai_message=summary,  # Store summary in AI message
                user_message="[SESSION_ENDED]",
                feedback=None
            )
            db.add(end_session)
            db.commit()
            
            return {
                "status": "ended", 
                "interview_id": interview_id, 
                "session_run_id": str(session_run_id),
                "summary": summary
            }
        
        return {"status": "ended", "interview_id": interview_id, "session_run_id": None}
        
    except Exception as e:
        print(f"[ERROR] Error ending interview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to end interview: {str(e)}")


@app.get("/api/interviews/{interview_id}/latest-session")
async def get_latest_session(
    request: Request,
    interview_id: str,
    user_info: Optional[dict] = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    """
    Get the most recent session for an interview
    Used to check if the last run was ended or to resume the correct run
    """
    # Handle OPTIONS preflight
    if request.method == "OPTIONS" or user_info is None:
        return Response(status_code=200)
    
    clerk_user_id = user_info["user_id"]
    
    user = db.query(User).filter(User.user_id == clerk_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == user.user_id
    ).first()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    latest_session = db.query(InterviewSession).filter(
        InterviewSession.interview_id == interview.id
    ).order_by(InterviewSession.created_at.desc()).first()
    
    if not latest_session:
        return None
        
    return latest_session.to_dict()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

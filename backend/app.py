from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from engine.adaptive_engine import next_question, score_response
from models.session import SessionState
from typing import Dict
from datetime import datetime, timedelta
import uuid
import os
import logging
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Adaptive Python Assessment API")

# Configure CORS - uses environment variable for production
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:3000,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage - in production, use Redis or database
SESSIONS: Dict[str, SessionState] = {}


class AnswerRequest(BaseModel):
    """Request model for answer submission."""
    student_answer: str = Field(..., min_length=1, max_length=5000)
    explanation: str = Field(..., min_length=1, max_length=5000)
    session_id: str = Field(..., description="Session ID from /start endpoint")
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate that session_id is a valid UUID."""
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid session ID format')
        return v


# Session cleanup thread
def cleanup_expired_sessions():
    """Remove sessions that have been inactive for over 1 hour."""
    while True:
        time.sleep(300)  # Check every 5 minutes
        try:
            current_time = datetime.now()
            expired = [
                sid for sid, session in SESSIONS.items()
                if current_time - session.last_activity > timedelta(hours=1)
            ]
            for sid in expired:
                del SESSIONS[sid]
                logger.info(f"Cleaned up expired session: {sid}")
            
            if expired:
                logger.info(f"Removed {len(expired)} expired sessions")
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")


# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_expired_sessions, daemon=True)
cleanup_thread.start()
logger.info("Session cleanup thread started")


@app.on_event("startup")
async def startup_event():
    """Validate required environment variables and API connections on startup."""
    logger.info("Starting Adaptive Python Assessment API...")
    
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    
    # Test OpenAI API connection
    try:
        from engine.scoring import client
        client.models.list()
        logger.info("OpenAI API connection validated successfully")
    except Exception as e:
        logger.error(f"OpenAI API validation failed: {e}")
        raise RuntimeError(f"OpenAI API key validation failed: {e}")
    
    logger.info("API startup complete - ready to accept requests")


@app.get("/start")
def start():
    """Start a new assessment session."""
    try:
        # Create new session with unique ID
        session_id = str(uuid.uuid4())
        session = SessionState()
        SESSIONS[session_id] = session
        
        logger.info(f"New session started: {session_id}")
        
        question = next_question(session)
        
        if question is None:
            logger.error(f"Failed to load initial question for session {session_id}")
            raise HTTPException(status_code=500, detail="Failed to load initial question")
        
        return {
            "session_id": session_id,
            "question": question
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting assessment: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting assessment: {str(e)}")


@app.post("/answer")
def answer(request: AnswerRequest):
    """Submit an answer and get evaluation with next question."""
    try:
        # Retrieve session
        session = SESSIONS.get(request.session_id)
        if not session:
            logger.warning(f"Session not found: {request.session_id}")
            raise HTTPException(status_code=404, detail="Session not found. Please start a new assessment.")
        
        # Update last activity time
        session.last_activity = datetime.now()
        
        if session.finished:
            logger.warning(f"Attempt to submit answer to finished session: {request.session_id}")
            raise HTTPException(status_code=400, detail="Assessment already completed")
        
        # Validate current question exists
        if not session.current_question:
            logger.error(f"No active question in session: {request.session_id}")
            raise HTTPException(status_code=400, detail="No active question")
        
        # Score the response
        response_data = {
            "student_answer": request.student_answer,
            "explanation": request.explanation
        }
        evaluation = score_response(session, response_data)
        
        logger.info(f"Session {request.session_id}: Question {session.question_number - 1} scored - {evaluation.get('final_score', 0):.2f}")
        
        # Check if assessment is finished
        if session.finished:
            summary = session.summary()
            logger.info(f"Session {request.session_id} completed - Final score: {summary['final_score']:.2f}")
            # Clean up session after completion
            del SESSIONS[request.session_id]
            return {
                "evaluation": evaluation,
                "finished": True,
                "summary": summary
            }
        
        # Get next question
        next_q = next_question(session)
        return {
            "evaluation": evaluation,
            "finished": False,
            "next_question": next_q
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing answer for session {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing answer: {str(e)}")


@app.get("/session/{session_id}")
def get_session_status(session_id: str):
    """Get current session status."""
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "question_number": session.question_number,
        "max_questions": session.max_questions,
        "bloom_level": session.bloom_level,
        "difficulty": session.difficulty,
        "finished": session.finished
    }


@app.delete("/session/{session_id}")
def end_session(session_id: str):
    """End a session early."""
    if session_id in SESSIONS:
        logger.info(f"Session manually ended: {session_id}")
        del SESSIONS[session_id]
        return {"message": "Session ended"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/health")
def health_check():
    """Health check endpoint with dependency validation."""
    health = {
        "status": "healthy",
        "active_sessions": len(SESSIONS)
    }
    
    # Check OpenAI API connection
    try:
        from engine.scoring import client
        client.models.list()
        health["openai_status"] = "connected"
    except Exception as e:
        health["openai_status"] = "disconnected"
        health["openai_error"] = str(e)
        health["status"] = "degraded"
        logger.warning(f"OpenAI API health check failed: {e}")
    
    return health

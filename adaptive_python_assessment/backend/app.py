from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from engine.adaptive_engine import next_question, score_response
from models.session import SessionState
from typing import Dict
import uuid

app = FastAPI(title="Adaptive Python Assessment API")

# Configure CORS - restrict this in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Specify allowed origins
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


@app.get("/start")
def start():
    """Start a new assessment session."""
    try:
        # Create new session with unique ID
        session_id = str(uuid.uuid4())
        session = SessionState()
        SESSIONS[session_id] = session
        
        question = next_question(session)
        
        if question is None:
            raise HTTPException(status_code=500, detail="Failed to load initial question")
        
        return {
            "session_id": session_id,
            "question": question
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting assessment: {str(e)}")


@app.post("/answer")
def answer(request: AnswerRequest):
    """Submit an answer and get evaluation with next question."""
    try:
        # Retrieve session
        session = SESSIONS.get(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found. Please start a new assessment.")
        
        if session.finished:
            raise HTTPException(status_code=400, detail="Assessment already completed")
        
        # Validate current question exists
        if not session.current_question:
            raise HTTPException(status_code=400, detail="No active question")
        
        # Score the response
        response_data = {
            "student_answer": request.student_answer,
            "explanation": request.explanation
        }
        evaluation = score_response(session, response_data)
        
        # Check if assessment is finished
        if session.finished:
            summary = session.summary()
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
        del SESSIONS[session_id]
        return {"message": "Session ended"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "active_sessions": len(SESSIONS)}

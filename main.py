from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from typing import Optional
import uvicorn

import config
from models.schemas import (
    SessionStartRequest, SessionResponse, ScreenAnalysisRequest,
    AudioTranscriptionRequest, QuestionRequest, QuestionResponse,
    AnswerSubmission, EvaluationRequest, EvaluationResponse,
    ErrorResponse, InterviewSession, SessionStatus, ScreenContent,
    AudioSegment, Answer, QuestionType
)
from services.ocr_service import OCRService
from services.stt_service import STTService
from services.ai_interviewer import AIInterviewer
from services.evaluator import EvaluatorService
from utils.helpers import session_manager, generate_question_id

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Interview System API",
    description="Automated interviewer for project presentations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ocr_service = OCRService()
stt_service = STTService()
ai_interviewer = AIInterviewer()
evaluator_service = EvaluatorService()

# Routes

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AI Interview System",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/session/start", response_model=SessionResponse)
async def start_session(request: SessionStartRequest):
    """Start a new interview session"""
    try:
        # Create new session
        session = InterviewSession(
            session_id=f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            student_name=request.student_name,
            project_title=request.project_title,
            status=SessionStatus.ACTIVE
        )
        
        # Store session
        session_manager.sessions[session.session_id] = session
        
        logger.info(f"Started session: {session.session_id}")
        
        return SessionResponse(
            session_id=session.session_id,
            status="success",
            message="Interview session started successfully"
        )
    
    except Exception as e:
        logger.error(f"Error starting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/screen/analyze")
async def analyze_screen(request: ScreenAnalysisRequest):
    """Analyze screen capture with OCR"""
    try:
        # Get session
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Analyze screen
        result = ocr_service.analyze_screen(request.image_base64)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail="OCR analysis failed")
        
        # Create screen content record
        screen_content = ScreenContent(
            extracted_text=result["extracted_text"],
            content_type=result["content_type"],
            metadata=result["metadata"]
        )
        
        # Add to session
        session.screen_contents.append(screen_content)
        
        logger.info(f"Screen analyzed for session {request.session_id}: {result['content_type']}")
        
        return {
            "success": True,
            "content_type": result["content_type"],
            "text_length": len(result["extracted_text"]),
            "metadata": result["metadata"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing screen: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/audio/transcribe")
async def transcribe_audio(request: AudioTranscriptionRequest):
    """Transcribe audio to text"""
    try:
        # Get session
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Transcribe audio
        result = stt_service.transcribe(request.audio_base64)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail="Transcription failed")
        
        # Create audio segment record
        audio_segment = AudioSegment(
            transcription=result["transcription"],
            duration=result["duration"]
        )
        
        # Add to session
        session.audio_segments.append(audio_segment)
        
        logger.info(f"Audio transcribed for session {request.session_id}: {len(result['transcription'])} chars")
        
        return {
            "success": True,
            "transcription": result["transcription"],
            "duration": result["duration"],
            "language": result["language"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/question", response_model=QuestionResponse)
async def get_next_question(request: QuestionRequest):
    """Generate next interview question"""
    try:
        # Get session
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Check if max questions reached
        if len(session.questions) >= config.MAX_QUESTIONS:
            raise HTTPException(status_code=400, detail="Maximum questions reached")
        
        # Determine question type
        question_type = QuestionType.INITIAL
        if len(session.questions) > 0 and request.include_follow_up:
            # Check if follow-up needed
            last_question = session.questions[-1]
            last_answer = next((a for a in session.answers if a.question_id == last_question.id), None)
            
            if last_answer and ai_interviewer.should_ask_followup(
                last_answer.answer_text,
                last_question.expected_topics
            ):
                question_type = QuestionType.FOLLOW_UP
        
        # Generate question
        question = ai_interviewer.generate_question(session, question_type)
        
        # Add to session
        session.questions.append(question)
        
        logger.info(f"Generated question for session {request.session_id}: {question.question_text}")
        
        return QuestionResponse(
            question=question,
            total_questions_asked=len(session.questions)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/answer")
async def submit_answer(request: AnswerSubmission):
    """Submit answer to a question"""
    try:
        # Get session
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Verify question exists
        question = next((q for q in session.questions if q.id == request.question_id), None)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Create answer record
        answer = Answer(
            question_id=request.question_id,
            answer_text=request.answer_text,
            duration=0.0  # Could be calculated from audio duration
        )
        
        # Add to session
        session.answers.append(answer)
        
        logger.info(f"Answer submitted for session {request.session_id}, question {request.question_id}")
        
        return {
            "success": True,
            "message": "Answer recorded successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting answer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/evaluate", response_model=EvaluationResponse)
async def evaluate_session(request: EvaluationRequest):
    """Evaluate completed interview session"""
    try:
        # Get session
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update session status
        session.status = SessionStatus.COMPLETED
        session.end_time = datetime.utcnow()
        
        # Generate evaluation
        evaluation = evaluator_service.evaluate_session(session)
        
        # Store evaluation in session
        session.evaluation = evaluation
        
        # Generate session summary
        session_summary = {
            "session_id": session.session_id,
            "duration_minutes": evaluation.total_duration / 60,
            "questions_asked": evaluation.total_questions,
            "screens_analyzed": len(session.screen_contents),
            "overall_score": evaluation.score.overall_score
        }
        
        logger.info(f"Session evaluated: {request.session_id}, score: {evaluation.score.overall_score:.2f}")
        
        return EvaluationResponse(
            evaluation=evaluation,
            session_summary=session_summary
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        success = session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"success": True, "message": "Session deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions"""
    try:
        sessions = session_manager.list_sessions()
        return {"sessions": sessions, "count": len(sessions)}
    
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )

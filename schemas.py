from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class QuestionType(str, Enum):
    INITIAL = "initial"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification"
    DEEP_DIVE = "deep_dive"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"

class ScreenContent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    extracted_text: str
    content_type: str  # "slide", "code", "diagram", "other"
    image_data: Optional[str] = None
    metadata: Dict[str, Any] = {}

class AudioSegment(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    transcription: str
    duration: float
    confidence: Optional[float] = None

class Question(BaseModel):
    id: str
    question_text: str
    question_type: QuestionType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Optional[str] = None
    expected_topics: List[str] = []

class Answer(BaseModel):
    question_id: str
    answer_text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration: float

class EvaluationScore(BaseModel):
    technical_depth: float = Field(..., ge=0, le=100)
    clarity: float = Field(..., ge=0, le=100)
    originality: float = Field(..., ge=0, le=100)
    understanding: float = Field(..., ge=0, le=100)
    overall_score: float = Field(..., ge=0, le=100)
    
class DetailedFeedback(BaseModel):
    strengths: List[str]
    improvements: List[str]
    specific_notes: Dict[str, str]
    recommendations: List[str]

class Evaluation(BaseModel):
    session_id: str
    score: EvaluationScore
    feedback: DetailedFeedback
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_questions: int
    total_duration: float

class InterviewSession(BaseModel):
    session_id: str
    student_name: Optional[str] = None
    project_title: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: SessionStatus = SessionStatus.ACTIVE
    screen_contents: List[ScreenContent] = []
    audio_segments: List[AudioSegment] = []
    questions: List[Question] = []
    answers: List[Answer] = []
    evaluation: Optional[Evaluation] = None

class SessionStartRequest(BaseModel):
    student_name: Optional[str] = None
    project_title: Optional[str] = None

class ScreenAnalysisRequest(BaseModel):
    session_id: str
    image_base64: str
    content_type: Optional[str] = "auto"

class AudioTranscriptionRequest(BaseModel):
    session_id: str
    audio_base64: str

class QuestionRequest(BaseModel):
    session_id: str
    include_follow_up: bool = True

class AnswerSubmission(BaseModel):
    session_id: str
    question_id: str
    answer_text: str

class EvaluationRequest(BaseModel):
    session_id: str

# Response Models
class SessionResponse(BaseModel):
    session_id: str
    status: str
    message: str

class QuestionResponse(BaseModel):
    question: Question
    total_questions_asked: int

class EvaluationResponse(BaseModel):
    evaluation: Evaluation
    session_summary: Dict[str, Any]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

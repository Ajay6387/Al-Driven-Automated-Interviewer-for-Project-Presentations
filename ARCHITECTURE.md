# System Architecture

## Overview

The AI Interview System is a full-stack application that conducts adaptive technical interviews by analyzing screen content and speech in real-time.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌──────────────┬──────────────┬────────────────────────┐  │
│  │Screen Capture│Audio Recorder│  Interview Panel       │  │
│  └──────────────┴──────────────┴────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  API Endpoints                        │  │
│  └────┬──────────┬──────────┬──────────┬────────────────┘  │
│       │          │          │          │                    │
│  ┌────▼────┐┌───▼────┐┌────▼────┐┌───▼──────┐            │
│  │   OCR   ││  STT   ││   AI    ││Evaluator │            │
│  │ Service ││Service ││Interview││ Service  │            │
│  └─────────┘└────────┘└─────────┘└──────────┘            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │  Claude API    │
                  │  (Anthropic)   │
                  └────────────────┘
```

## Component Details

### Frontend Components

#### 1. ScreenCapture Component
- **Purpose**: Capture and send screen content
- **Technology**: navigator.mediaDevices.getDisplayMedia()
- **Frequency**: Every 5 seconds
- **Output**: Base64 encoded PNG images

#### 2. AudioRecorder Component
- **Purpose**: Record and transcribe user speech
- **Technology**: MediaRecorder API
- **Frequency**: 10-second chunks
- **Output**: Base64 encoded audio (WebM)

#### 3. InterviewPanel Component
- **Purpose**: Display questions and collect answers
- **Features**: 
  - Progress tracking
  - Real-time Q&A
  - Answer submission

#### 4. EvaluationReport Component
- **Purpose**: Display final evaluation results
- **Features**:
  - Score visualization
  - Detailed feedback
  - Recommendations

### Backend Services

#### 1. OCR Service
- **Technology**: Tesseract OCR
- **Preprocessing**: 
  - Grayscale conversion
  - Thresholding
  - Denoising
- **Content Detection**:
  - Code snippets
  - Slides
  - Diagrams
- **Output**: Extracted text + metadata

#### 2. STT Service
- **Technology**: OpenAI Whisper
- **Model**: Base (configurable)
- **Features**:
  - Audio decoding
  - Transcription
  - Keyword extraction
- **Output**: Text transcription + confidence

#### 3. AI Interviewer Service
- **Technology**: Claude API (Sonnet 4.5)
- **Features**:
  - Context-aware question generation
  - Follow-up detection
  - Question type classification
- **Question Types**:
  - Initial
  - Follow-up
  - Clarification
  - Deep-dive

#### 4. Evaluator Service
- **Technology**: Claude API
- **Evaluation Criteria**:
  - Technical Depth (30%)
  - Clarity (25%)
  - Originality (25%)
  - Understanding (20%)
- **Output**: Scores + detailed feedback

## Data Flow

### 1. Session Start
```
User → Frontend → POST /api/session/start → Backend
Backend → Create Session → Return session_id
```

### 2. Screen Analysis
```
ScreenCapture → Base64 Image → POST /api/screen/analyze
Backend → OCR Service → Extract Text
Backend → Store in Session → Return metadata
```

### 3. Audio Processing
```
AudioRecorder → Base64 Audio → POST /api/audio/transcribe
Backend → STT Service → Transcribe
Backend → Store in Session → Return transcription
```

### 4. Question Generation
```
Frontend → POST /api/interview/question
Backend → Build Context (screens + audio)
Backend → Claude API → Generate Question
Backend → Store Question → Return to Frontend
```

### 5. Answer Submission
```
Frontend → POST /api/interview/answer
Backend → Store Answer
Backend → Determine if follow-up needed
Backend → Trigger next question or evaluation
```

### 6. Evaluation
```
Frontend → POST /api/session/evaluate
Backend → Compile all session data
Backend → Claude API → Generate evaluation
Backend → Return scores + feedback
```

## Session Management

### Session Data Structure
```python
InterviewSession {
    session_id: str
    student_name: str
    project_title: str
    start_time: datetime
    status: SessionStatus
    screen_contents: List[ScreenContent]
    audio_segments: List[AudioSegment]
    questions: List[Question]
    answers: List[Answer]
    evaluation: Evaluation
}
```

### Storage
- **Current**: In-memory dictionary
- **Production**: Redis or PostgreSQL recommended

## API Endpoints

### Session Management
- `POST /api/session/start` - Start new session
- `GET /api/session/{id}` - Get session details
- `DELETE /api/session/{id}` - Delete session
- `GET /api/sessions` - List all sessions

### Content Analysis
- `POST /api/screen/analyze` - Analyze screen capture
- `POST /api/audio/transcribe` - Transcribe audio

### Interview
- `POST /api/interview/question` - Get next question
- `POST /api/interview/answer` - Submit answer

### Evaluation
- `POST /api/session/evaluate` - Generate evaluation

## Security Considerations

### Current Implementation
- CORS enabled for development
- No authentication (add in production)
- API key stored in environment variables

### Production Recommendations
1. **Authentication**: JWT tokens
2. **Authorization**: Role-based access control
3. **Rate Limiting**: Prevent API abuse
4. **Input Validation**: Sanitize all inputs
5. **HTTPS**: Encrypt data in transit
6. **API Key Rotation**: Regular key updates

## Performance Optimization

### Current Bottlenecks
1. OCR processing (2-5 seconds per image)
2. Whisper transcription (1-3 seconds per chunk)
3. Claude API calls (1-2 seconds per request)

### Optimization Strategies
1. **Async Processing**: Use background workers
2. **Caching**: Cache common OCR results
3. **Batching**: Batch Claude API calls
4. **CDN**: Serve static assets via CDN
5. **Database Indexing**: For session queries

## Scalability

### Horizontal Scaling
- Use load balancer (nginx/AWS ALB)
- Stateless backend services
- Shared session storage (Redis)

### Vertical Scaling
- Increase OCR/STT processing power
- Optimize Claude API usage
- Database query optimization

## Monitoring & Logging

### Metrics to Track
- API response times
- OCR success rate
- Transcription accuracy
- Question generation time
- Session completion rate
- Error rates

### Logging Levels
- INFO: Normal operations
- WARNING: Non-critical issues
- ERROR: Failures requiring attention
- DEBUG: Development debugging

## Future Enhancements

1. **Real-time Collaboration**: Multiple interviewers
2. **Video Recording**: Save presentation videos
3. **Advanced Analytics**: Detailed presentation insights
4. **Custom Question Banks**: Domain-specific questions
5. **Multi-language Support**: Interview in any language
6. **Integration**: LMS/ATS integrations
7. **Mobile App**: Native iOS/Android apps

## Technology Stack Summary

### Frontend
- React 18
- Axios for API calls
- WebRTC for media capture

### Backend
- FastAPI (Python 3.11)
- Tesseract OCR
- OpenAI Whisper
- Anthropic Claude API
- Pydantic for validation

### Infrastructure
- Docker/Docker Compose
- Nginx (production)
- AWS/Heroku (deployment)

---

For implementation details, see README.md and DEPLOYMENT.md

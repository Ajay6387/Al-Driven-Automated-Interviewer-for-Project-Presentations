# 🎯 AI-Driven Automated Interviewer for Project Presentations

A complete AI system that conducts adaptive interviews by analyzing student project presentations through screen sharing and speech recognition.

## 🌟 Features

- **Real-time Screen Analysis**: OCR extraction from slides, code, and diagrams
- **Speech-to-Text**: Live transcription of student presentations
- **Adaptive Interviewing**: Context-aware questions based on content
- **Smart Evaluation**: Scores on technical depth, clarity, originality, and understanding
- **Live Dashboard**: Real-time presentation monitoring and Q&A

## 🏗️ Architecture

```
Frontend (React + WebRTC)
    ↓
Backend API (FastAPI)
    ↓
Processing Pipeline:
    → Screen Capture + OCR (Tesseract)
    → Audio → STT (Whisper)
    → Content Analysis (Claude API)
    → Question Generation
    → Response Evaluation
```

## 📋 Prerequisites

- Python 3.9+
- Node.js 16+
- Anthropic API Key (for Claude)
- FFmpeg (for audio processing)

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:
```env
ANTHROPIC_API_KEY=your_api_key_here
PORT=8000
```

Run backend:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

Create `.env` file:
```env
REACT_APP_API_URL=http://localhost:8000
```

Run frontend:
```bash
npm start
```

Visit: http://localhost:3000

## 📁 Project Structure

```
ai-interviewer-system/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── services/
│   │   ├── ocr_service.py      # Screen OCR processing
│   │   ├── stt_service.py      # Speech-to-text
│   │   ├── ai_interviewer.py   # AI question generation
│   │   └── evaluator.py        # Scoring engine
│   ├── models/
│   │   └── schemas.py          # Data models
│   ├── utils/
│   │   └── helpers.py          # Utility functions
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ScreenCapture.jsx
│   │   │   ├── AudioRecorder.jsx
│   │   │   ├── InterviewPanel.jsx
│   │   │   └── EvaluationReport.jsx
│   │   ├── App.jsx
│   │   └── index.jsx
│   └── package.json
└── README.md
```

## 🎮 How to Use

1. **Start Presentation**: Click "Start Interview" and share your screen
2. **Present Your Project**: Speak naturally while showing slides/code
3. **Answer Questions**: AI will ask adaptive questions based on your content
4. **Get Feedback**: Receive detailed evaluation at the end

## 🧪 Testing

### Test the Backend
```bash
cd backend
pytest tests/
```

### Test the Frontend
```bash
cd frontend
npm test
```

## 🔧 Configuration

### AI Model Settings
Edit `backend/config.py`:
- `MODEL_NAME`: Claude model to use (default: claude-sonnet-4-5-20250929)
- `MAX_QUESTIONS`: Maximum questions per session
- `EVALUATION_CRITERIA`: Scoring weights

### OCR Settings
- `OCR_LANG`: Language for OCR (default: eng)
- `OCR_DPI`: Image DPI for processing

## 📊 Evaluation Metrics

The system scores presentations on:
- **Technical Depth (30%)**: Implementation complexity and understanding
- **Clarity (25%)**: Communication and explanation quality
- **Originality (25%)**: Innovation and unique approaches
- **Understanding (20%)**: Response quality and problem-solving

## 🌐 API Endpoints

- `POST /api/session/start` - Start interview session
- `POST /api/screen/analyze` - Analyze screen capture
- `POST /api/audio/transcribe` - Transcribe audio
- `POST /api/interview/question` - Get next question
- `POST /api/session/evaluate` - Get final evaluation
- `GET /api/session/{id}` - Get session details

## 🐛 Troubleshooting

**Issue**: OCR not working
- Solution: Install Tesseract: `brew install tesseract` (Mac) or `apt-get install tesseract-ocr` (Linux)

**Issue**: Audio recording fails
- Solution: Grant microphone permissions in browser

**Issue**: WebSocket connection fails
- Solution: Check CORS settings in backend and firewall rules

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

MIT License - feel free to use for your hackathon and beyond!

## 👥 Team

Built for [Your Hackathon Name] - [Your Team Name]

## 🙏 Acknowledgments

- Anthropic Claude API for AI capabilities
- OpenAI Whisper for speech recognition
- Tesseract OCR for text extraction

---

**Good luck with your hackathon! 🚀**

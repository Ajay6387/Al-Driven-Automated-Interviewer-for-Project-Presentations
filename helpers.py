import uuid
from datetime import datetime
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return f"session_{uuid.uuid4().hex[:12]}"

def generate_question_id(session_id: str, question_number: int) -> str:
    """Generate a unique question ID"""
    return f"{session_id}_q{question_number}"

def format_timestamp(dt: datetime = None) -> str:
    """Format datetime to ISO string"""
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat()

def calculate_duration(start_time: datetime, end_time: datetime = None) -> float:
    """Calculate duration in seconds"""
    if end_time is None:
        end_time = datetime.utcnow()
    return (end_time - start_time).total_seconds()

def validate_base64(data: str) -> bool:
    """Validate base64 encoded string"""
    try:
        import base64
        base64.b64decode(data)
        return True
    except Exception:
        return False

def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def extract_metadata(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract useful metadata from session"""
    return {
        "total_screens": len(session_data.get("screen_contents", [])),
        "total_audio_segments": len(session_data.get("audio_segments", [])),
        "total_questions": len(session_data.get("questions", [])),
        "total_answers": len(session_data.get("answers", [])),
        "session_status": session_data.get("status", "unknown")
    }

class SessionManager:
    """In-memory session manager (use database in production)"""
    
    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        logger.info("SessionManager initialized")
    
    def create_session(self, session_data: Dict[str, Any]) -> str:
        """Create a new session"""
        session_id = generate_session_id()
        self.sessions[session_id] = session_data
        logger.info(f"Created session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            logger.info(f"Updated session: {session_id}")
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False
    
    def list_sessions(self) -> list:
        """List all session IDs"""
        return list(self.sessions.keys())
    
    def cleanup_old_sessions(self, max_age_seconds: int = 3600):
        """Remove sessions older than max_age_seconds"""
        current_time = datetime.utcnow()
        to_delete = []
        
        for session_id, session_data in self.sessions.items():
            start_time = session_data.get("start_time")
            if start_time:
                age = (current_time - start_time).total_seconds()
                if age > max_age_seconds:
                    to_delete.append(session_id)
        
        for session_id in to_delete:
            self.delete_session(session_id)
        
        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} old sessions")

# Global session manager instance
session_manager = SessionManager()

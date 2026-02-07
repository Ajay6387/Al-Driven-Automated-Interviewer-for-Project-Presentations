import whisper
import base64
import io
import logging
from pydub import AudioSegment
import numpy as np
import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

class STTService:
    """Service for converting speech to text using Whisper"""
    
    def __init__(self):
        self.model_name = config.WHISPER_MODEL
        logger.info(f"Loading Whisper model: {self.model_name}")
        self.model = whisper.load_model(self.model_name)
        logger.info("Whisper model loaded successfully")
    
    def decode_audio(self, audio_base64: str) -> np.ndarray:
        """
        Decode base64 audio to numpy array
        
        Args:
            audio_base64: Base64 encoded audio string
            
        Returns:
            Numpy array of audio samples
        """
        try:
            # Decode base64
            audio_data = base64.b64decode(audio_base64)
            
            # Load audio using pydub
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
            
            # Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Set sample rate to 16kHz (Whisper requirement)
            audio = audio.set_frame_rate(16000)
            
            # Convert to numpy array
            samples = np.array(audio.get_array_of_samples()).astype(np.float32) / 32768.0
            
            return samples
            
        except Exception as e:
            logger.error(f"Audio decoding failed: {str(e)}")
            raise
    
    def transcribe(self, audio_base64: str, language: str = "en") -> dict:
        """
        Transcribe audio to text
        
        Args:
            audio_base64: Base64 encoded audio string
            language: Language code (default: "en")
            
        Returns:
            Dictionary with transcription and metadata
        """
        try:
            # Decode audio
            audio_array = self.decode_audio(audio_base64)
            
            # Calculate duration
            duration = len(audio_array) / 16000.0
            
            # Transcribe using Whisper
            result = self.model.transcribe(
                audio_array,
                language=language,
                task="transcribe",
                fp16=False
            )
            
            transcription = result["text"].strip()
            
            logger.info(f"Transcribed {duration:.2f}s of audio: {transcription[:50]}...")
            
            return {
                "transcription": transcription,
                "duration": duration,
                "language": result.get("language", language),
                "segments": result.get("segments", []),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return {
                "transcription": "",
                "duration": 0.0,
                "language": language,
                "segments": [],
                "success": False,
                "error": str(e)
            }
    
    def extract_keywords(self, transcription: str) -> list:
        """Extract important keywords from transcription"""
        # Simple keyword extraction
        words = transcription.lower().split()
        
        # Filter out common words (simple stopword removal)
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
                     'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
                     'this', 'that', 'these', 'those', 'i', 'you', 'we', 'they', 'it'}
        
        keywords = [word for word in words if word not in stopwords and len(word) > 3]
        
        # Return unique keywords
        return list(set(keywords))[:15]
    
    def detect_confidence_issues(self, segments: list) -> list:
        """Detect parts of transcription with low confidence"""
        low_confidence_parts = []
        
        for segment in segments:
            # Whisper doesn't always provide confidence scores
            # We can use other heuristics like repetition, filler words
            text = segment.get("text", "").lower()
            
            # Check for filler words or repetitions
            filler_words = ['um', 'uh', 'er', 'ah', 'like', 'you know']
            if any(filler in text for filler in filler_words):
                low_confidence_parts.append({
                    "text": segment.get("text"),
                    "start": segment.get("start"),
                    "end": segment.get("end")
                })
        
        return low_confidence_parts

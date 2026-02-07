import anthropic
from typing import List, Dict, Any, Optional
import logging
import json
import config
from models.schemas import Question, QuestionType, InterviewSession, ScreenContent, AudioSegment

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

class AIInterviewer:
    """AI-powered interviewer using Claude API for adaptive questioning"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.CLAUDE_MODEL
        
    def _build_context(self, session: InterviewSession) -> str:
        """Build context from session data for Claude"""
        context_parts = []
        
        # Add project information
        if session.project_title:
            context_parts.append(f"Project: {session.project_title}")
        
        # Add screen content summary
        if session.screen_contents:
            recent_screens = session.screen_contents[-5:]  # Last 5 screens
            screen_summary = "\n".join([
                f"[{sc.content_type.upper()}] {sc.extracted_text[:200]}..."
                for sc in recent_screens
            ])
            context_parts.append(f"\nRecent Screen Content:\n{screen_summary}")
        
        # Add transcription summary
        if session.audio_segments:
            recent_audio = session.audio_segments[-5:]  # Last 5 segments
            audio_summary = " ".join([seg.transcription for seg in recent_audio])
            context_parts.append(f"\nStudent's Recent Speech:\n{audio_summary}")
        
        # Add previous Q&A
        if session.questions and session.answers:
            qa_pairs = []
            for q in session.questions[-3:]:  # Last 3 questions
                answer = next((a for a in session.answers if a.question_id == q.id), None)
                if answer:
                    qa_pairs.append(f"Q: {q.question_text}\nA: {answer.answer_text}")
            if qa_pairs:
                context_parts.append(f"\nPrevious Q&A:\n" + "\n\n".join(qa_pairs))
        
        return "\n\n".join(context_parts)
    
    def generate_question(
        self,
        session: InterviewSession,
        question_type: QuestionType = QuestionType.INITIAL
    ) -> Question:
        """
        Generate an adaptive question based on session context
        
        Args:
            session: Current interview session
            question_type: Type of question to generate
            
        Returns:
            Generated Question object
        """
        context = self._build_context(session)
        
        # Determine question count
        questions_asked = len(session.questions)
        
        system_prompt = """You are an expert technical interviewer conducting a project presentation interview. 
Your role is to:
1. Ask insightful, context-aware questions based on what the student is presenting
2. Probe for technical depth and understanding
3. Ask follow-up questions when answers are incomplete
4. Evaluate originality and implementation details
5. Be encouraging but thorough

Generate questions that are:
- Specific to the content shown (code, slides, diagrams)
- Appropriate for the interview stage
- Clear and focused
- Designed to reveal depth of understanding"""

        user_prompt = f"""Based on the following presentation context, generate a {question_type.value} question.

{context}

Questions asked so far: {questions_asked}/{config.MAX_QUESTIONS}

Requirements:
- Make the question specific to what you see in the screen content and hear in the speech
- If this is a follow-up, build on previous answers
- Focus on technical implementation, design decisions, or problem-solving
- Keep questions concise and clear

Return ONLY a JSON object with this structure:
{{
    "question_text": "Your question here",
    "context": "Brief context explaining why you're asking this",
    "expected_topics": ["topic1", "topic2"]
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parse response
            response_text = response.content[0].text.strip()
            
            # Extract JSON from response
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text
            
            question_data = json.loads(json_str)
            
            question = Question(
                id=f"q_{questions_asked + 1}",
                question_text=question_data["question_text"],
                question_type=question_type,
                context=question_data.get("context"),
                expected_topics=question_data.get("expected_topics", [])
            )
            
            logger.info(f"Generated question: {question.question_text}")
            return question
            
        except Exception as e:
            logger.error(f"Question generation failed: {str(e)}")
            # Fallback question
            return Question(
                id=f"q_{questions_asked + 1}",
                question_text="Can you explain the main technical challenge you faced in this project?",
                question_type=QuestionType.INITIAL,
                context="Fallback question",
                expected_topics=["challenges", "problem-solving"]
            )
    
    def should_ask_followup(self, answer_text: str, expected_topics: List[str]) -> bool:
        """Determine if a follow-up question is needed based on answer quality"""
        if not answer_text or len(answer_text.split()) < 10:
            return True  # Too short
        
        # Check if expected topics are covered
        answer_lower = answer_text.lower()
        topics_covered = sum(1 for topic in expected_topics if topic.lower() in answer_lower)
        
        if topics_covered < len(expected_topics) * 0.5:
            return True  # Less than 50% of topics covered
        
        return False
    
    def analyze_presentation_flow(self, session: InterviewSession) -> Dict[str, Any]:
        """Analyze the overall presentation for insights"""
        return {
            "total_screens": len(session.screen_contents),
            "code_screens": sum(1 for sc in session.screen_contents if sc.content_type == "code"),
            "slide_screens": sum(1 for sc in session.screen_contents if sc.content_type == "slide"),
            "total_speech_duration": sum(seg.duration for seg in session.audio_segments),
            "avg_answer_length": sum(len(a.answer_text.split()) for a in session.answers) / len(session.answers) if session.answers else 0,
            "questions_asked": len(session.questions)
        }

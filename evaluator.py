import anthropic
from typing import Dict, Any
import logging
import json
import config
from models.schemas import (
    InterviewSession, EvaluationScore, DetailedFeedback, 
    Evaluation
)

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

class EvaluatorService:
    """Service for evaluating student presentations and generating scores"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.CLAUDE_MODEL
        self.weights = config.EVALUATION_WEIGHTS
    
    def _prepare_evaluation_context(self, session: InterviewSession) -> str:
        """Prepare comprehensive context for evaluation"""
        context_parts = []
        
        # Project info
        context_parts.append(f"Project: {session.project_title or 'Not specified'}")
        context_parts.append(f"Student: {session.student_name or 'Anonymous'}")
        
        # Content analysis
        total_screens = len(session.screen_contents)
        code_screens = sum(1 for sc in session.screen_contents if sc.content_type == "code")
        
        context_parts.append(f"\nPresentation Overview:")
        context_parts.append(f"- Total screens shared: {total_screens}")
        context_parts.append(f"- Code demonstrations: {code_screens}")
        context_parts.append(f"- Questions answered: {len(session.answers)}")
        
        # Screen content summary
        if session.screen_contents:
            context_parts.append("\nKey Content Shown:")
            for i, sc in enumerate(session.screen_contents[:10], 1):
                context_parts.append(f"{i}. [{sc.content_type}] {sc.extracted_text[:150]}...")
        
        # Q&A Summary
        if session.questions and session.answers:
            context_parts.append("\nInterview Q&A:")
            for q in session.questions:
                answer = next((a for a in session.answers if a.question_id == q.id), None)
                if answer:
                    context_parts.append(f"\nQ: {q.question_text}")
                    context_parts.append(f"A: {answer.answer_text}")
        
        return "\n".join(context_parts)
    
    def evaluate_session(self, session: InterviewSession) -> Evaluation:
        """
        Evaluate the entire interview session
        
        Args:
            session: Completed interview session
            
        Returns:
            Evaluation object with scores and feedback
        """
        context = self._prepare_evaluation_context(session)
        
        system_prompt = """You are an expert evaluator of student technical presentations and projects.
Your role is to provide fair, constructive, and detailed evaluation based on:

1. Technical Depth (30%): Implementation complexity, technical knowledge, problem-solving approach
2. Clarity (25%): Communication skills, explanation quality, presentation organization
3. Originality (25%): Innovation, unique approaches, creative solutions
4. Understanding (20%): Grasp of concepts, ability to answer questions, depth of knowledge

Provide scores on a 0-100 scale and detailed, constructive feedback."""

        user_prompt = f"""Evaluate this student's project presentation:

{context}

Provide a comprehensive evaluation in the following JSON format:
{{
    "scores": {{
        "technical_depth": <0-100>,
        "clarity": <0-100>,
        "originality": <0-100>,
        "understanding": <0-100>
    }},
    "strengths": ["strength1", "strength2", "strength3"],
    "improvements": ["improvement1", "improvement2", "improvement3"],
    "specific_notes": {{
        "technical": "detailed note about technical aspects",
        "communication": "detailed note about communication",
        "innovation": "detailed note about innovation"
    }},
    "recommendations": ["recommendation1", "recommendation2", "recommendation3"]
}}

Be specific, fair, and constructive in your evaluation."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=config.MAX_TOKENS,
                temperature=0.3,  # Lower temperature for more consistent evaluation
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parse response
            response_text = response.content[0].text.strip()
            
            # Extract JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text
            
            eval_data = json.loads(json_str)
            
            # Calculate overall score
            scores = eval_data["scores"]
            overall_score = (
                scores["technical_depth"] * self.weights["technical_depth"] +
                scores["clarity"] * self.weights["clarity"] +
                scores["originality"] * self.weights["originality"] +
                scores["understanding"] * self.weights["understanding"]
            )
            
            # Create evaluation objects
            score = EvaluationScore(
                technical_depth=scores["technical_depth"],
                clarity=scores["clarity"],
                originality=scores["originality"],
                understanding=scores["understanding"],
                overall_score=overall_score
            )
            
            feedback = DetailedFeedback(
                strengths=eval_data["strengths"],
                improvements=eval_data["improvements"],
                specific_notes=eval_data["specific_notes"],
                recommendations=eval_data["recommendations"]
            )
            
            # Calculate session duration
            if session.end_time and session.start_time:
                duration = (session.end_time - session.start_time).total_seconds()
            else:
                duration = sum(seg.duration for seg in session.audio_segments)
            
            evaluation = Evaluation(
                session_id=session.session_id,
                score=score,
                feedback=feedback,
                total_questions=len(session.questions),
                total_duration=duration
            )
            
            logger.info(f"Session evaluated. Overall score: {overall_score:.2f}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            # Return default evaluation
            return self._create_default_evaluation(session)
    
    def _create_default_evaluation(self, session: InterviewSession) -> Evaluation:
        """Create a default evaluation when AI evaluation fails"""
        score = EvaluationScore(
            technical_depth=70.0,
            clarity=70.0,
            originality=70.0,
            understanding=70.0,
            overall_score=70.0
        )
        
        feedback = DetailedFeedback(
            strengths=["Completed the presentation", "Answered questions"],
            improvements=["Could not generate detailed evaluation"],
            specific_notes={"error": "Automatic evaluation unavailable"},
            recommendations=["Review the recording for self-assessment"]
        )
        
        duration = sum(seg.duration for seg in session.audio_segments)
        
        return Evaluation(
            session_id=session.session_id,
            score=score,
            feedback=feedback,
            total_questions=len(session.questions),
            total_duration=duration
        )
    
    def generate_feedback_summary(self, evaluation: Evaluation) -> str:
        """Generate a human-readable summary of the evaluation"""
        summary_parts = []
        
        summary_parts.append(f"Overall Score: {evaluation.score.overall_score:.1f}/100")
        summary_parts.append("\nScore Breakdown:")
        summary_parts.append(f"- Technical Depth: {evaluation.score.technical_depth:.1f}/100")
        summary_parts.append(f"- Clarity: {evaluation.score.clarity:.1f}/100")
        summary_parts.append(f"- Originality: {evaluation.score.originality:.1f}/100")
        summary_parts.append(f"- Understanding: {evaluation.score.understanding:.1f}/100")
        
        summary_parts.append("\nStrengths:")
        for strength in evaluation.feedback.strengths:
            summary_parts.append(f"✓ {strength}")
        
        summary_parts.append("\nAreas for Improvement:")
        for improvement in evaluation.feedback.improvements:
            summary_parts.append(f"• {improvement}")
        
        summary_parts.append("\nRecommendations:")
        for rec in evaluation.feedback.recommendations:
            summary_parts.append(f"→ {rec}")
        
        return "\n".join(summary_parts)

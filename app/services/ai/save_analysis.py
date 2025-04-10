from datetime import datetime
from bson import ObjectId
import logging
from typing import Dict, Any, Optional, List

# Set up logger
logger = logging.getLogger(__name__)

def generate_candidate_feedback(
    facial_result_or_summary: Dict[str, Any],
    speech_result: Optional[Dict[str, Any]] = None
) -> str:
    facial_summary = {}

    # Safely extract facial summary
    if isinstance(facial_result_or_summary, dict):
        summary_candidate = facial_result_or_summary.get("summary", facial_result_or_summary)
        if isinstance(summary_candidate, dict):
            facial_summary = summary_candidate
        else:
            logger.warning("⚠️ Unexpected structure: facial_result_or_summary['summary'] is not a dict")

    # Safely get top_3 emotions
    top_emotions = facial_summary.get("top_3", [])
    common_emotion = top_emotions[0][0] if top_emotions and isinstance(top_emotions[0], (list, tuple)) else "neutral"

    feedback = f"You appeared mostly {common_emotion} during the interview. "

    if speech_result:
        speech_data = speech_result.get("data", speech_result)
        speech_score = speech_data.get("speech_score", 0)

        feedback += f"Your speech clarity score was {speech_score}/10. "
        if speech_score > 7:
            feedback += "You spoke confidently. "
        else:
            feedback += "Try to speak more clearly next time. "

    feedback += "Overall, you performed decently. Keep practicing for improvement."
    logger.info(f"Generated candidate feedback: {feedback}")
    return feedback


def generate_ai_suggestions(
    facial_summary: Dict[str, float], 
    speech_summary: Dict[str, str], 
    user_experience_level: str = "beginner", 
    custom_thresholds: Dict[str, float] = None
) -> List[str]:
    # Generates AI-driven feedback based on facial expressions and speech analysis
    
    suggestions = []

    # Define default thresholds
    thresholds = {
        "eye_contact": 0.6,
        "smile_ratio": 0.2,
        "blink_rate": 0.3,
        "speech_rate": 2.0,
        "sentiment_negative_threshold": 0.4
    }

    # Override thresholds if custom values are provided
    if custom_thresholds:
        thresholds.update(custom_thresholds)

    def analyze_facial_expressions(facial_summary: Dict[str, float]):
        # Analyzes facial expressions and provides actionable suggestions
        if facial_summary.get("eye_contact", 1.0) < thresholds["eye_contact"]:
            suggestions.append("Focus on the interviewer’s face to maintain steady eye contact.")
        if facial_summary.get("smile_ratio", 0.0) < thresholds["smile_ratio"]:
            suggestions.append("Try smiling more—it helps build rapport and convey warmth.")
        if facial_summary.get("blink_rate", 0.0) > thresholds["blink_rate"]:
            suggestions.append("Reduce excessive blinking to appear composed and confident.")

    def analyze_speech_patterns(speech_summary: Dict[str, str]):
        # Evaluates speech characteristics and offers improvements
        if speech_summary.get("intonation") == "monotone":
            suggestions.append("Vary your tone to make conversations more engaging.")
        if speech_summary.get("overall_sentiment_score", 1.0) < thresholds["sentiment_negative_threshold"]:
            suggestions.append("Try using more positive expressions to leave a strong impression.")
        if speech_summary.get("speech_rate", 0.0) > thresholds["speech_rate"]:
            suggestions.append("Slow down slightly to enhance clarity and comprehension.")

    # Apply dynamic feedback tone
    if user_experience_level == "advanced":
        suggestions = [f"Consider refining your approach: {s}" for s in suggestions]
    elif user_experience_level == "beginner":
        suggestions = [f"Here’s a helpful tip: {s}" for s in suggestions]

    # Perform analysis
    analyze_facial_expressions(facial_summary)
    analyze_speech_patterns(speech_summary)

    # Provide positive reinforcement if no issues are detected
    if not suggestions:
        suggestions.append("Fantastic job! Your communication skills are impressive.")

    logger.info(f"Generated AI suggestions: {suggestions}")
    return suggestions

async def save_interview_analysis_to_db(
    db,
    user_id: str,
    interview_id: str,
    facial_result: dict,
    speech_result: Optional[dict] = None
) -> Optional[Dict[str, Any]]:
    try:
        # Validate inputs
        if not isinstance(interview_id, str) or not interview_id.strip():
            raise ValueError("Invalid interview_id")

        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("Invalid user_id")
        
        # Use the facial_result directly
        facial_summary = {}
        if isinstance(facial_result, dict):
            summary_candidate = facial_result.get("summary", facial_result)
            if isinstance(summary_candidate, dict):
                facial_summary = summary_candidate
            else:
                logger.warning("⚠️ facial_result['summary'] is not a dict — skipping")

        # Extract speech summary safely
        speech_summary = {}
        if isinstance(speech_result, dict):
            summary = speech_result.get("summary", {})
            if not isinstance(summary, dict):
                logger.warning("⚠️ speech_result['summary'] is not a dict — skipping")
                summary = {}

            speech_summary = {
                "overall_sentiment": summary.get("overall_sentiment") or speech_result.get("overall_sentiment"),
                "intonation": summary.get("intonation") or speech_result.get("intonation"),
                "overall_sentiment_score": summary.get("overall_sentiment_score", 1.0),
                "speech_rate": summary.get("speech_rate", 0.0)
            }

        # Ensure speech summary values are not null
        if not speech_summary.get("overall_sentiment"):
            logger.warning("⚠️ Missing overall_sentiment in speech_result; defaulting to 'neutral'.")
            speech_summary["overall_sentiment"] = "neutral"

        if not speech_summary.get("intonation"):
            logger.warning("⚠️ Missing intonation in speech_result; defaulting to 'unknown'.")
            speech_summary["intonation"] = "neutral"
        # Log speech summary for debugging
        logger.debug(f"Speech summary after fallback check: {speech_summary}")

        # Generate AI feedback payload
        feedback_payload = {
            "facial_summary": facial_summary,
            "speech_summary": speech_summary,
            "suggestions": generate_ai_suggestions(facial_summary, speech_summary),
            "candidate_feedback": generate_candidate_feedback(facial_result, speech_result),
            "timestamp": datetime.utcnow()
        }

        logger.info(f"Saving interview analysis for interview_id: {interview_id} to DB.")
        # Save full analysis to separate collection
        await db["interview_analysis"].insert_one({
            "user_id": user_id,
            "interview_id": interview_id,
            "facial_analysis": facial_result,  # Save facial_result directly
            "facial_summary": facial_summary,
            "speech_analysis": speech_result,
            "ai_feedback": feedback_payload,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        # Update the main interview document
        update_result = await db["interviews"].update_one(
            {"_id": interview_id, "user_id": user_id},
            {
                "$set": {
                    "status": "analyzed",
                    "feedback": feedback_payload,
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "status_history": "analyzed"
                }
            }
        )

        # Check for modifications
        if update_result.modified_count == 0:
            logger.warning(f"⚠️ No interview updated for interview_id: {interview_id}")

        logger.info(f"✅ Saved AI analysis for interview_id: {interview_id}")
        return feedback_payload

    except Exception as e:
        logger.error(f"❌ Error saving interview analysis for interview_id: {interview_id}, user_id: {user_id} - {str(e)}")
        return None

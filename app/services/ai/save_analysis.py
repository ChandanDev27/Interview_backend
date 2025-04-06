from datetime import datetime
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

async def save_interview_analysis_to_db(db, user_id: str, interview_id: str, facial_result: dict, speech_result: dict):
    try:
        if not ObjectId.is_valid(interview_id):
            raise ValueError("Invalid interview_id")

        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("Invalid user_id")

        interview_obj_id = ObjectId(interview_id)

        # Combine AI feedback
        full_feedback = {
            "facial_summary": facial_result.get("summary", "No facial summary available."),
            "speech_summary": speech_result.get("summary", "No speech summary available."),
            "suggestions": [
                "Try to maintain eye contact",
                "Speak a bit slower for clarity",
                "Work on reducing filler words"
            ],
            "timestamp": datetime.utcnow()
        }

        update_data = {
            "$set": {
                "ai_analysis.facial": facial_result,
                "ai_analysis.speech": speech_result,
                "feedback": full_feedback,
                "status": "analyzed",
                "updated_at": datetime.utcnow()
            },
            "$push": {
                "status_history": "analyzed"
            }
        }

        result = await db["interviews"].update_one(
            {"_id": interview_obj_id, "user_id": user_id},
            update_data
        )

        if result.modified_count == 0:
            logger.warning(f"No document updated for interview_id: {interview_id}")
        else:
            logger.info(f"✅ AI analysis saved for interview_id: {interview_id}")

        return full_feedback

    except Exception as e:
        logger.error(f"❌ Error saving AI analysis: {str(e)}")
        return None

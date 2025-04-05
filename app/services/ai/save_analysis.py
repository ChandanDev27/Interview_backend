from datetime import datetime
from bson import ObjectId

async def save_interview_analysis_to_db(db, user_id, interview_id, facial_result, speech_result):
    try:
        interview_obj_id = ObjectId(interview_id)

        # Combine facial and speech insights
        full_feedback = {
            "facial_summary": facial_result.get("summary"),
            "speech_summary": speech_result.get("summary"),
            "suggestions": [
                "Try to maintain eye contact",
                "Speak a bit slower for clarity",
                "Work on reducing filler words"
            ],
            "timestamp": datetime.utcnow()
        }

        # Store in DB
        await db["interviews"].update_one(
            {"_id": interview_obj_id, "user_id": user_id},
            {
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
        )

        return full_feedback

    except Exception as e:
        raise Exception(f"Error saving analysis: {str(e)}")

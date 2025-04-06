from datetime import datetime
from bson import ObjectId
import logging
from app.database import get_database
from app.schemas.interview import InterviewModel

logger = logging.getLogger(__name__)


async def create_interview(user_id: str, candidate_name: str, questions: list):
    try:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("Invalid user_id")

        if not isinstance(candidate_name, str) or not candidate_name.strip():
            raise ValueError("Invalid candidate_name")

        if not isinstance(questions, list) or not questions:
            raise ValueError("Questions must be a non-empty list")

        new_interview = InterviewModel(
            user_id=user_id,
            candidate_name=candidate_name,
            questions=questions,
            responses=[None] * len(questions),
            feedback=None,
            status="pending",
            ai_feedback=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            status_history=["pending"]
        ).dict()

        db = await get_database()
        result = await db["interviews"].insert_one(new_interview)

        logger.info(f"✅ Interview created for user_id: {user_id}")
        return str(result.inserted_id)

    except Exception as e:
        logger.exception(f"❌ Error creating interview: {str(e)}")
        return None


async def get_interviews_by_user(user_id: str):
    try:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("Invalid user_id")

        db = await get_database()
        interviews = await db["interviews"].find({"user_id": user_id}).to_list(100)

        for interview in interviews:
            interview["id"] = str(interview["_id"])
            interview.pop("_id", None)

        return interviews

    except Exception as e:
        logger.exception(f"❌ Error fetching interviews for user_id {user_id}: {str(e)}")
        return []

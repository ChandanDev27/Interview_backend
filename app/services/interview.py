from datetime import datetime
from bson import ObjectId
import logging
from typing import Optional, List
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


async def get_interviews_by_user(user_id: str, skip: int = 0, limit: int = 10) -> List[dict]:
    try:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("Invalid user_id")

        db = await get_database()
        interviews = await db["interviews"].find({"user_id": user_id}).skip(skip).limit(limit).to_list(length=limit)

        for interview in interviews:
            interview["id"] = str(interview["_id"])
            interview.pop("_id", None)

        return interviews

    except Exception as e:
        logger.exception(f"❌ Error fetching interviews for user_id {user_id}: {str(e)}")
        return []


async def get_interview_by_id(interview_id: str) -> Optional[dict]:
    try:
        db = await get_database()
        interview = await db["interviews"].find_one({"_id": ObjectId(interview_id)})

        if not interview:
            return None

        interview["id"] = str(interview["_id"])
        interview.pop("_id", None)
        return interview

    except Exception as e:
        logger.exception(f"❌ Error fetching interview by ID {interview_id}: {str(e)}")
        return None


async def update_interview_status(interview_id: str, new_status: str) -> bool:
    try:
        db = await get_database()
        update = {
            "$set": {"status": new_status, "updated_at": datetime.utcnow()},
            "$push": {"status_history": new_status}
        }
        result = await db["interviews"].update_one({"_id": ObjectId(interview_id)}, update)
        return result.modified_count == 1

    except Exception as e:
        logger.exception(f"❌ Failed to update interview status for {interview_id}: {str(e)}")
        return False


async def update_ai_feedback(interview_id: str, ai_feedback: list) -> bool:
    try:
        db = await get_database()
        result = await db["interviews"].update_one(
            {"_id": ObjectId(interview_id)},
            {"$set": {"ai_feedback": ai_feedback, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count == 1

    except Exception as e:
        logger.exception(f"❌ Failed to update AI feedback for {interview_id}: {str(e)}")
        return False


async def update_response(interview_id: str, question_index: int, response: dict) -> bool:
    try:
        db = await get_database()
        update = {
            f"responses.{question_index}": response,
            "updated_at": datetime.utcnow()
        }
        result = await db["interviews"].update_one(
            {"_id": ObjectId(interview_id)},
            {"$set": update}
        )
        return result.modified_count == 1

    except Exception as e:
        logger.exception(f"❌ Failed to update response for question {question_index} in interview {interview_id}: {str(e)}")
        return False

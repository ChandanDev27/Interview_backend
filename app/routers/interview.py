from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime
import logging

from app.database import get_database
from ..schemas.interview import (
    InterviewCreate,
    InterviewResponse,
    ResponseSubmission,
    AIAnalysis,
)
from ..services.auth import get_current_user
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interviews", tags=["Interviews"])


@router.on_event("startup")
async def ensure_indexes():
    # Ensures MongoDB indexes on startup.
    db = await get_database()
    await db["interviews"].create_index([("user_id", 1)])
    db = await get_database()
    await db["interviews"].create_index([("created_at", 1)])


# ✅ Get all interviews for a user

@router.get("/", response_model=List[InterviewResponse])
async def get_interviews(current_user: dict = Depends(get_current_user)):
    # Retrieves all interviews for the logged-in user.
    db = await get_database()
    user_id = str(current_user["client_id"])
    interviews = await db["interviews"].find({"user_id": user_id}).to_list(length=100)

    return [InterviewResponse(**{**i, "id": str(i["_id"])}) for i in interviews]


# ✅ Create an interview
@router.post("/", response_model=InterviewResponse)
async def create_interview(
    interview: InterviewCreate, current_user: dict = Depends(get_current_user)
):
    # Creates a new interview for the user.
    try:
        db = await get_database()

        interview_data = interview.model_dump()
        interview_data.update(
            {
                "user_id": str(current_user["client_id"]),
                "responses": [],
                "feedback": None,
                "status": "pending",
                "status_history": ["pending"],
                "created_at": datetime.utcnow(),
            }
        )

        result = await db["interviews"].insert_one(interview_data)
        interview_data["id"] = str(result.inserted_id)

        logger.info(f"✅ Interview created for user: {current_user['client_id']}")
        return InterviewResponse(**interview_data)

    except Exception as e:
        logger.exception(f"❌ Error creating interview: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# ✅ Submit response
@router.post("/{interview_id}/responses/")
async def submit_response(
    interview_id: str,
    response_data: ResponseSubmission,
    current_user: dict = Depends(get_current_user),
):
    # Allows the user to submit responses to an interview.
    try:
        db = await get_database()
        user_id = str(current_user["client_id"])

        # ✅ Validate ObjectId format
        try:
            interview_obj_id = ObjectId(interview_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid interview ID format")

        result = await db["interviews"].update_one(
            {"_id": interview_obj_id, "user_id": user_id},
            {
                "$push": {
                    "responses": {"$each": response_data.responses},
                    "status_history": {"$each": ["completed"]},
                },
                "$set": {
                    "status": "completed",
                    "updated_at": datetime.utcnow(),
                },
            },
        )

        if result.matched_count == 0:
            logger.warning(f"⚠️ Interview not found: {interview_id}")
            raise HTTPException(
                status_code=404, detail="Interview not found or not authorized"
            )

        logger.info(f"✅ Responses recorded for interview: {interview_id}")
        return {"message": "Responses recorded successfully"}

    except Exception as e:
        logger.exception(f"❌ Error submitting response: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# ✅ Store AI feedback
@router.post("/{interview_id}/analyze/")
async def store_ai_feedback(
    interview_id: str,
    feedback_data: AIAnalysis,
    current_user: dict = Depends(get_current_user),
):
    # Stores AI-generated feedback for an interview.
    try:
        db = await get_database()
        user_id = str(current_user["client_id"])

        # ✅ Validate ObjectId format
        try:
            interview_obj_id = ObjectId(interview_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid interview ID format")

        feedback_entry = {
            "feedback": feedback_data.feedback,
            "timestamp": datetime.utcnow(),
        }

        result = await db["interviews"].update_one(
            {"_id": interview_obj_id, "user_id": user_id},
            {
                "$push": {"ai_feedback": feedback_entry},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

        if result.matched_count == 0:
            logger.warning(
                f"⚠️ AI feedback: Interview not found: {interview_id}"
            )
            raise HTTPException(
                status_code=404, detail="Interview not found or not authorized"
            )

        logger.info(f"✅ AI feedback stored for interview: {interview_id}")
        return {"message": "AI feedback stored successfully"}

    except Exception as e:
        logger.exception(f"❌ Error storing AI feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

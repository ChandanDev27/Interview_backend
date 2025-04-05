from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import List
import logging
import tempfile
import os

from app.services.ai.save_analysis import save_interview_analysis_to_db
from app.database import get_database
from ..schemas.interview import (
    InterviewCreate,
    InterviewResponse,
    ResponseSubmission,
    AIAnalysis,
    AIFeedbackEntry
)
from ..services.auth import get_current_user
from app.services.ai.facial_analysis import extract_framewise_emotions, analyze_speech

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interviews", tags=["Interviews"])


@router.on_event("startup")
async def ensure_indexes():
    db = await get_database()
    await db["interviews"].create_index([("user_id", 1)])
    await db["interviews"].create_index([("created_at", 1)])


@router.get("/", response_model=List[InterviewResponse])
async def get_interviews(current_user: dict = Depends(get_current_user)):
    db = await get_database()
    user_id = str(current_user["client_id"])
    interviews = await db["interviews"].find({"user_id": user_id}).to_list(length=100)
    return [InterviewResponse(**{**i, "id": str(i["_id"])}) for i in interviews]


@router.post("/", response_model=InterviewResponse)
async def create_interview(
    interview: InterviewCreate, current_user: dict = Depends(get_current_user)
):
    try:
        db = await get_database()

        interview_data = interview.model_dump()
        interview_data.update({
            "user_id": str(current_user["client_id"]),
            "responses": [],
            "feedback": None,
            "ai_feedback": [],
            "status": "pending",
            "status_history": ["pending"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        result = await db["interviews"].insert_one(interview_data)
        interview_data["id"] = str(result.inserted_id)

        logger.info(f"✅ Interview created for user: {current_user['client_id']}")
        return InterviewResponse(**interview_data)

    except Exception as e:
        logger.exception(f"❌ Error creating interview: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/{interview_id}/responses/")
async def submit_response(
    interview_id: str,
    response_data: ResponseSubmission,
    current_user: dict = Depends(get_current_user),
):
    try:
        db = await get_database()
        user_id = str(current_user["client_id"])

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
            raise HTTPException(status_code=404, detail="Interview not found or not authorized")

        logger.info(f"✅ Responses recorded for interview: {interview_id}")
        return {"message": "Responses recorded successfully"}

    except Exception as e:
        logger.exception(f"❌ Error submitting response: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/{interview_id}/analyze/")
async def store_ai_feedback(
    interview_id: str,
    feedback_data: AIAnalysis,
    current_user: dict = Depends(get_current_user),
):
    try:
        db = await get_database()
        user_id = str(current_user["client_id"])

        try:
            interview_obj_id = ObjectId(interview_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid interview ID format")

        feedback_entry = AIFeedbackEntry(
            feedback=feedback_data.feedback,
            timestamp=datetime.utcnow()
        ).model_dump()

        result = await db["interviews"].update_one(
            {"_id": interview_obj_id, "user_id": user_id},
            {
                "$push": {"ai_feedback": feedback_entry},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

        if result.matched_count == 0:
            logger.warning(f"⚠️ AI feedback: Interview not found: {interview_id}")
            raise HTTPException(status_code=404, detail="Interview not found or not authorized")

        logger.info(f"✅ AI feedback stored for interview: {interview_id}")
        return {"message": "AI feedback stored successfully"}

    except Exception as e:
        logger.exception(f"❌ Error storing AI feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/interview/{interview_id}/analyze/final")
async def finalize_interview_analysis(
    interview_id: str,
    user_id: str = Form(...),
    video: UploadFile = File(...),
    audio: UploadFile = File(...),
    db=Depends(get_database)
):
    video_path = audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(await video.read())
            video_path = temp_video.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(await audio.read())
            audio_path = temp_audio.name

        facial_result = extract_framewise_emotions(video_path)
        speech_result = await analyze_speech(audio_path)

        feedback = await save_interview_analysis_to_db(
            db, user_id, interview_id, facial_result, speech_result
        )

        return {
            "message": "Interview analysis complete",
            "feedback_for_candidate": feedback,
            "facial_analysis": facial_result,
            "speech_analysis": speech_result
        }

    except Exception as e:
        logger.error(f"Final interview analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Final analysis failed")

    finally:
        try:
            video.file.close()
            audio.file.close()
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception as cleanup_err:
            logger.warning(f"Cleanup warning: {str(cleanup_err)}")


@router.post("/analyze-facial-expression/")
async def analyze_facial_expression_api(
    video: UploadFile = File(...),
    user_id: str = Form(...),
    interview_id: str = Form(...),
    db=Depends(get_database)
):
    video_path = None
    try:
        try:
            user_obj_id = ObjectId(user_id)
            interview_obj_id = ObjectId(interview_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid ObjectId format")

        if not video.filename.endswith((".mp4", ".avi", ".mov")):
            raise HTTPException(status_code=400, detail="Invalid video format")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(await video.read())
            video_path = temp_video.name

        analysis_result = extract_framewise_emotions(video_path)

        analysis_doc = {
            "user_id": user_obj_id,
            "interview_id": interview_obj_id,
            "result": analysis_result,
            "created_at": datetime.utcnow()
        }

        await db["facial_analysis"].insert_one(analysis_doc)

        return {"message": "Analysis complete", "data": analysis_result}

    except Exception as e:
        logger.error(f"❌ Facial expression DB save failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Facial analysis failed: {str(e)}")

    finally:
        try:
            video.file.close()
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
        except Exception as cleanup_err:
            logger.warning(f"Cleanup warning: {str(cleanup_err)}")

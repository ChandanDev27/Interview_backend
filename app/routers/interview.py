from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import List
import logging
import subprocess
import tempfile
import os
from app.database import get_database
from ..schemas.interview import (
    InterviewCreate,
    InterviewResponse,
    ResponseSubmission,
    AIAnalysis,
    AIFeedbackEntry
)
from ..services.utils import extract_audio_from_video, get_video_duration
from ..services.ai.save_analysis import save_interview_analysis_to_db
from ..services.auth import get_current_user
from ..services.ai.facial_analysis import extract_framewise_emotions
from ..services.ai.ai_analysis import analyze_video_audio
from ..services.ai.speech_analysis import analyze_speech
from motor.motor_asyncio import AsyncIOMotorDatabase

ALLOWED_VIDEO_MIME_TYPES = {"video/mp4", "video/x-msvideo", "video/quicktime", "video/webm"}
ALLOWED_AUDIO_MIME_TYPES = {"audio/wav", "audio/x-wav"}

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interviews", tags=["Interviews"])


@router.get("/", response_model=List[InterviewResponse])
async def get_interviews(current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_database)):
    user_id = str(current_user["client_id"])
    interviews = await db["interviews"].find({"user_id": user_id}).to_list(length=100)
    return [InterviewResponse(**{**i, "id": str(i["_id"])}) for i in interviews]


@router.post("/", response_model=InterviewResponse)
async def create_interview(interview: InterviewCreate, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_database)):
    try:
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
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        user_id = str(current_user["client_id"])
        interview_obj_id = ObjectId(interview_id)

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
            logger.warning(f"⚠️ Interview not found or unauthorized: {interview_id}")
            raise HTTPException(status_code=404, detail="Interview not found or not authorized")

        logger.info(f"✅ Responses recorded for interview: {interview_id}")
        return {"status": "success", "message": "Responses recorded successfully"}

    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid interview ID format")
    except Exception as e:
        logger.exception(f"❌ Error submitting response: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/{interview_id}/analyze/")
async def store_ai_feedback(
    interview_id: str,
    feedback_data: AIAnalysis,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        user_id = str(current_user["client_id"])
        interview_obj_id = ObjectId(interview_id)

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
        return {"status": "success", "message": "AI feedback stored successfully"}

    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid interview ID format")
    except Exception as e:
        logger.exception(f"❌ Error storing AI feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def convert_webm_to_mp4(webm_path: str) -> str:
    mp4_path = f"{os.path.splitext(webm_path)[0]}.mp4"
    command = [
        "ffmpeg",
        "-y",
        "-i", webm_path,
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        mp4_path
    ]
    try:
        subprocess.run(command, check=True)
        return mp4_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"WebM to MP4 conversion failed: {e}")


@router.post("/{interview_id}/analyze/final")
async def finalize_interview_analysis(
    interview_id: str,
    user_id: str = Form(...),
    video: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    webm_path = video_path = audio_path = None
    try:
        interview = await db["interviews"].find_one({"_id": ObjectId(interview_id), "user_id": user_id})
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found or unauthorized")

        if video.content_type not in ALLOWED_VIDEO_MIME_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported video MIME type")

        # Save uploaded video
        ext = ".webm" if "webm" in video.content_type else ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_video:
            temp_video.write(await video.read())
            webm_path = temp_video.name

        # Convert if needed
        if ext == ".webm":
            video_path = convert_webm_to_mp4(webm_path)
        else:
            video_path = webm_path

        # 🔍 Duration validation
        duration = get_video_duration(video_path)
        if duration < 1:
            raise HTTPException(status_code=400, detail="Video too short or invalid.")

        # Extract audio
        audio_path = extract_audio_from_video(video_path)

        # Analyze
        result = await analyze_video_audio(video_path, audio_path)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=f"Analysis failed: {result['message']}")

        # Save analysis
        feedback = await save_interview_analysis_to_db(
            db, user_id, interview_id,
            facial_result=result["data"]["facial_analysis"],
            speech_result=result["data"]["speech_analysis"]
        )

        return {
            "status": "success",
            "message": "Interview analysis complete",
            "feedback_for_candidate": feedback,
            "facial_analysis": result["data"]["facial_analysis"],
            "facial_summary": result["data"]["facial_summary"],
            "speech_analysis": result["data"]["speech_analysis"]
        }

    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        logger.error(f"❌ Final interview analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Final analysis failed")
    finally:
        try:
            video.file.close()
            if webm_path and os.path.exists(webm_path):
                os.remove(webm_path)
            if video_path and os.path.exists(video_path) and video_path != webm_path:
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
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    video_path = None
    try:
        user_obj_id = ObjectId(user_id)
        interview_obj_id = ObjectId(interview_id)

        if video.content_type not in ALLOWED_VIDEO_MIME_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported video MIME type")

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

        return {
            "status": "success",
            "message": "Facial expression analysis complete",
            "data": analysis_result
        }

    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")
    except Exception as e:
        logger.error(f"❌ Facial expression DB save failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Facial analysis failed")
    finally:
        try:
            video.file.close()
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
        except Exception as cleanup_err:
            logger.warning(f"Cleanup warning: {str(cleanup_err)}")

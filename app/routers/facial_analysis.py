from fastapi import APIRouter, HTTPException, File, UploadFile
from datetime import datetime
import shutil
import tempfile
import os
import logging
from app.services.ai.ai_analysis import analyze_video_audio
from app.services.ai.facial_analysis import (
    analyze_facial_expression,
)

router = APIRouter(prefix="/api", tags=["Facial & Speech Analysis"])

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_VIDEO_TYPES = {"video/mp4"}
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/x-wav"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}


# -----------------------------------------
# Facial Expression Analysis from Video File
# -----------------------------------------
@router.post("/analyze_facial")
async def analyze_facial(file: UploadFile = File(...)):
    temp_video_path = None
    try:
        if file.content_type not in ALLOWED_VIDEO_TYPES:
            raise HTTPException(status_code=400, detail="Only MP4 video files are allowed.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            shutil.copyfileobj(file.file, temp_video)
            temp_video_path = temp_video.name

        result = await analyze_facial_expression(temp_video_path)

        if result["status"] != "success":
            raise HTTPException(status_code=500, detail=result["message"])

        # Split data for frontend and internal use
        full_data = result["data"]
        summary_data = full_data.get("summary")

        return {
            "status": "success",
            "message": "Facial expression analysis completed.",
            "data": summary_data  # send only summary to frontend
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Facial analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        try:
            file.file.close()
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
        except Exception as cleanup_err:
            logger.warning(f"Cleanup warning: {str(cleanup_err)}")


# -----------------------------------------
# Combined Video + Audio Analysis
# -----------------------------------------
@router.post("/analyze_video_audio")
async def analyze_video_and_audio(
    video: UploadFile = File(...),
    audio: UploadFile = File(...),
):
    temp_video_path = None
    temp_audio_path = None
    try:
        # Validate video file type
        if video.content_type not in ALLOWED_VIDEO_TYPES:
            raise HTTPException(status_code=400, detail="Only MP4 video files are allowed.")

        # Validate audio file type
        if audio.content_type not in ALLOWED_AUDIO_TYPES:
            raise HTTPException(status_code=400, detail="Only WAV audio files are allowed.")

        # Save the uploaded video file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            shutil.copyfileobj(video.file, temp_video)
            temp_video_path = temp_video.name

        # Save the uploaded audio file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            shutil.copyfileobj(audio.file, temp_audio)
            temp_audio_path = temp_audio.name

        # Perform combined video + audio analysis
        result = await analyze_video_audio(temp_video_path, temp_audio_path)

        # Return the result of video + audio analysis
        return {"video_audio_analysis": result}

    except HTTPException as he:
        # Raise HTTP exceptions for invalid file types
        raise he

    except Exception as e:
        # Log other errors that occur during analysis
        logger.error(f"❌ Error analyzing video/audio: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        # Cleanup: close the uploaded files and remove temporary files
        try:
            video.file.close()
            audio.file.close()
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
        except Exception as cleanup_err:
            logger.warning(f"Cleanup warning: {str(cleanup_err)}")

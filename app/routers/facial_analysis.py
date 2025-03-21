from fastapi import APIRouter, File, UploadFile, HTTPException
import shutil
import tempfile
import os
import logging
from app.services.ai.ai_analysis import analyze_facial_expression

router = APIRouter(prefix="/api", tags=["Facial Analysis"])

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_VIDEO_TYPES = {"video/mp4"}


@router.post("/analyze_facial")
async def analyze_facial(file: UploadFile = File()):
    try:
        # Check MIME type
        unsupported_type_msg = "Only MP4 video files are allowed"
        if file.content_type not in ALLOWED_VIDEO_TYPES:
            logger.warning(f"🚨 Unsupported file type: {file.content_type}")
            raise HTTPException(status_code=400, detail=unsupported_type_msg)

        # Save video to a temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".mp4"
        ) as temp_video:
            shutil.copyfileobj(
                file.file, temp_video
            )
            temp_video_path = temp_video.name

        # Call AI model to analyze video
        emotion = await analyze_facial_expression(temp_video_path)

        # Cleanup temporary file
        os.remove(temp_video_path)

        # Return the result
        return {
            "facial_expression": emotion
        }

    except HTTPException as he:
        raise he  # Re-raise known HTTP errors
    except Exception as e:
        error_msg = f"❌ Error analyzing facial expression: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail="Internal Server Error")

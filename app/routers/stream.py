from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
import logging
from typing import Dict
from app.services.ai.facial_analysis import analyze_facial_expression_frame
# from app.services.auth import get_current_user

router = APIRouter(
    prefix="/api/stream",
    tags=["Video Streaming"]
)

logger = logging.getLogger(__name__)


@router.post("/frame", response_model=Dict[str, str])
async def receive_frame(
    file: UploadFile = File(...),
    # current_user: dict = Depends(get_current_user)
):
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No frame uploaded.")

    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Only JPEG and PNG formats are allowed."
        )

    try:
        logger.info(f"📸 Received frame: {file.filename}, Content-Type: {file.content_type}")
        result = await analyze_facial_expression_frame(file.file)
        logger.info(f"✅ Analysis result: {result}")
        return result

    except Exception as e:
        logger.exception(f"❌ Error analyzing frame: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to analyze frame.")

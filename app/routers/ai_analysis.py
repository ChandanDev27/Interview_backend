from fastapi import APIRouter, File, UploadFile, HTTPException
import logging
from app.services.ai.ai_analysis import analyze_facial_expression_frame

router = APIRouter(prefix="/api/ai", tags=["AI Analysis"])

# Setup logger
logger = logging.getLogger(__name__)

@router.post("/analyze-frame/")
async def analyze_frame(file: UploadFile = File(...)):
    try:
        # Check for file type (e.g., image, video)
        if not file.filename.endswith((".jpg", ".jpeg", ".png", ".mp4", ".avi")):
            raise HTTPException(status_code=400, detail="Invalid file type. Only image/video files are allowed.")
        
        result = await analyze_facial_expression_frame(file)
        logger.info(f"Frame analysis successful for file: {file.filename}")
        return {"message": "Frame analysis successful", "data": result}
    except HTTPException as http_err:
        logger.error(f"HTTP error: {http_err.detail}")
        raise http_err
    except Exception as e:
        logger.error(f"Error in frame analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Frame analysis failed: {str(e)}")

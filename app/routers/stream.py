from fastapi import APIRouter, UploadFile, File
from app.services.ai_analysis import analyze_facial_expression_frame

router = APIRouter(tags=["Video Streaming"])

@router.post("/frame")
async def receive_frame(file: UploadFile = File(...)):
    result = await analyze_facial_expression_frame(file.file)
    return result

from fastapi import APIRouter, File, UploadFile
from app.services.ai_analysis import analyze_facial_expression_frame

router = APIRouter()

@router.post("/analyze-frame/")
async def analyze_frame(file: UploadFile = File(...)):
    result = await analyze_facial_expression_frame(file)
    return result

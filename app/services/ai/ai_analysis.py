# ai_analysis.py
import asyncio
from typing import Dict, Any
from .facial_analysis import analyze_facial_expression
from .speech_analysis import analyze_speech

async def analyze_video_audio(video_path: str, audio_path: str) -> Dict[str, Any]:
    try:
        facial_result = await analyze_facial_expression(video_path)
        speech_result = await analyze_speech(audio_path)

        facial_summary = summarize_emotions(facial_result["data"]) if facial_result["data"] else {}

        return {
            "status": "success",
            "message": "Combined video and audio analysis completed.",
            "data": {
                "facial_analysis": facial_result["data"],
                "facial_summary": facial_summary,
                "speech_analysis": speech_result["data"]
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

import asyncio
from typing import Dict, Any, List
from collections import Counter
from fastapi.concurrency import run_in_threadpool
from .facial_analysis import analyze_facial_expression
from .speech_analysis import extract_audio_from_video
from app.services.ai.speech_analysis import analyze_speech
import logging

# Set up logger
logger = logging.getLogger(__name__)

async def analyze_video_audio(video_path: str, audio_path: str) -> Dict[str, Any]:
    try:
        logger.info(f"🔍 Starting combined analysis for video: {video_path} and audio: {audio_path}")
        
        # Initialize results to avoid uninitialized variable issues
        facial_result = {"status": "error", "data": None}
        speech_result = {"status": "error", "data": None}
        
        # Facial analysis
        logger.info("🎥 Analyzing facial expressions from video...")
        facial_result = await analyze_facial_expression(video_path)
        if facial_result.get("status") == "error":
            logger.warning(f"❌ Facial analysis failed for {video_path}: {facial_result.get('message')}")
        else:
            logger.info("✅ Facial analysis completed successfully.")
        
        # Speech analysis (run blocking function in threadpool)
        logger.info("🎙️ Analyzing speech from audio...")
        speech_result = await run_in_threadpool(analyze_speech, audio_path)
        if speech_result.get("status") == "error":
            logger.warning(f"❌ Speech analysis failed for {audio_path}: {speech_result.get('message')}")
        else:
            logger.info("✅ Speech analysis completed successfully.")

        # Summarize emotions if available
        facial_summary = summarize_emotions(facial_result["data"]) if facial_result.get("data") else {}
        
        logger.info("🔍 Combining results and preparing the final output.")

        return {
            "status": "success",
            "message": "Combined video and audio analysis completed.",
            "data": {
                "facial_analysis": facial_result.get("data", {}),
                "facial_summary": facial_summary,
                "speech_analysis": speech_result.get("data", {})
            }
        }

    except Exception as e:
        logger.error(f"❌ Error during combined video and audio analysis: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

def summarize_emotions(framewise_data: List[Dict]) -> Dict:
    if not framewise_data:
        return {"message": "No emotions detected in frames."}
    
    all_emotions = [f["dominant_emotion"] for f in framewise_data if f["dominant_emotion"] != "error"]
    
    if not all_emotions:
        return {"message": "No valid emotions detected."}
    
    # Count occurrences of each emotion
    emotion_counts = dict(Counter(all_emotions))
    total_frames = len(all_emotions)
    
    # Calculate percentage for each emotion
    emotion_percentage = {emotion: (count / total_frames) * 100 for emotion, count in emotion_counts.items()}
    
    # Get top 3 most common emotions
    most_common = Counter(all_emotions).most_common(3)

    # Adding timestamp data
    emotion_timestamps = {emotion: [f["time"] for f in framewise_data if f["dominant_emotion"] == emotion] 
                          for emotion in emotion_counts}

    return {
        "dominant_emotions": emotion_counts,
        "emotion_percentage": emotion_percentage,  # Percentage breakdown of each emotion
        "top_3": most_common,
        "emotion_timestamps": emotion_timestamps  # Emotions over time
    }

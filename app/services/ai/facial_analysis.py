import os
import cv2
import logging
import tempfile
from fastapi import UploadFile
from deepface import DeepFace
from collections import Counter
from typing import Dict, Any
from fastapi.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

# --------------------------------------------
# Frame-by-Frame Facial Emotion Extraction
# --------------------------------------------
def extract_framewise_emotions(video_path: str, seconds_between_frames: int = 1):  # 1 second interval
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Failed to open video file.")

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_interval = max(1, fps * seconds_between_frames)
    frame_count = 0
    framewise_results = []
    all_emotions = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            try:
                analysis = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False)
                dominant_emotion = analysis[0]["dominant_emotion"]
                all_emotions.append(dominant_emotion)
                framewise_results.append({
                    "time": round(frame_count / fps, 2),
                    "dominant_emotion": dominant_emotion,
                    "emotion_scores": analysis[0]["emotion"]
                })
            except Exception as e:
                logger.error(f"[ERROR] Frame {frame_count}: {str(e)}")
                framewise_results.append({
                    "time": round(frame_count / fps, 2),
                    "dominant_emotion": "error",  # indicate error in processing
                    "emotion_scores": {}
                })

        frame_count += 1

    cap.release()
    return framewise_results


# -------------------------------------------------
# Async Wrapper for Facial Expression Analysis
# -------------------------------------------------
async def analyze_facial_expression(video_path: str) -> Dict[str, Any]:
    try:
        # Running the emotion extraction in a thread pool to avoid blocking the event loop
        analysis_result = await run_in_threadpool(extract_framewise_emotions, video_path)
        return {
            "status": "success",
            "message": "Facial expression analysis completed.",
            "data": analysis_result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


# -------------------------------------------------
# Frame Facial Emotion Analysis (single image frame)
# -------------------------------------------------
async def analyze_facial_expression_frame(file: UploadFile) -> Dict[str, Any]:
    try:
        # Save frame temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(await file.read())
            temp_path = tmp.name

        # Ensure the file is a valid image (add further checks for file type/size if needed)
        analysis = DeepFace.analyze(img_path=temp_path, actions=["emotion"], enforce_detection=False)
        emotion_data = analysis[0]

        # Clean up the temporary file
        os.remove(temp_path)

        return {
            "status": "success",
            "message": "Frame emotion analysis completed.",
            "data": {
                "dominant_emotion": emotion_data["dominant_emotion"],
                "emotion_scores": emotion_data["emotion"]
            }
        }

    except Exception as e:
        logger.error(f"Error in frame analysis: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

import cv2
import logging
import numpy as np
from fastapi import UploadFile
import tempfile
from deepface import DeepFace
from collections import Counter
import speech_recognition as sr
from typing import Dict, Any, Optional
from bson import ObjectId
from datetime import datetime

logger = logging.getLogger(__name__)
# --------------------------------------------
# Frame-by-Frame Facial Emotion Extraction
# --------------------------------------------
def extract_framewise_emotions(video_path: str, seconds_between_frames: int = 3):
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

        frame_count += 1

    cap.release()
    return framewise_results
# -------------------------------------------------
# THIS is for extracting emotions from a video and give summarize
# -------------------------------------------------
def summarize_emotions(framewise_data):
    all_emotions = [f["dominant_emotion"] for f in framewise_data]
    emotion_counts = dict(Counter(all_emotions))
    most_common = Counter(all_emotions).most_common(3)

    return {
        "dominant_emotions": emotion_counts,
        "top_3": most_common
    }
# -------------------------------------------------
# Async Wrapper for Facial Analysis
# -------------------------------------------------
async def analyze_facial_expression(video_path: str) -> Dict[str, Any]:
    try:
        analysis_result = extract_framewise_emotions(video_path)
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

# --------------------------------------------
# Frame Facial Emotion Analysis (single image frame)
# --------------------------------------------
async def analyze_facial_expression_frame(file: UploadFile) -> Dict[str, Any]:
    try:
        # Save frame temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(await file.read())
            temp_path = tmp.name

        analysis = DeepFace.analyze(img_path=temp_path, actions=["emotion"], enforce_detection=False)
        emotion_data = analysis[0]

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

# -------------------------------------------------
# Async Wrapper for Audio Transcription
# -------------------------------------------------
async def analyze_speech(audio_path: str) -> Dict[str, Any]:
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            transcript = recognizer.recognize_google(audio)
            print("Transcript:", transcript)

            # Placeholder speech clarity score
            speech_score = 8  # You can replace this with a real metric later

            return {
                "status": "success",
                "message": "Speech transcription completed.",
                "data": {
                    "transcript": transcript,
                    "speech_score": speech_score
                }
            }

    except sr.UnknownValueError:
        return {
            "status": "error",
            "message": "Could not understand audio",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }

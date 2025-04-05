import cv2
import numpy as np
from deepface import DeepFace
from collections import Counter
import speech_recognition as sr
from typing import Dict, Any

# --------------------------------------------
# Facial Expression Analysis (Frame-by-Frame)
# --------------------------------------------
def extract_framewise_emotions(video_path: str) -> Dict[str, Any]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Failed to open video file.")

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_interval = max(1, fps // 2)
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
                    "time": frame_count // fps,
                    "dominant_emotion": dominant_emotion,
                    "emotion_scores": analysis[0]["emotion"]
                })
            except Exception as e:
                print(f"[ERROR] Frame {frame_count}: {str(e)}")

        frame_count += 1

    cap.release()

    emotion_counts = dict(Counter(all_emotions))
    most_common = Counter(all_emotions).most_common(3)
    return {
        "framewise_emotions": framewise_results,
        "summary": {
            "dominant_emotions": emotion_counts,
            "top_3": most_common
        }
    }


# -------------------------------------------------
# ✅ Async Wrapper for Facial Expression Analysis
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

# -------------------------------------------------
# ✅ Speech Emotion (via audio transcript)
# -------------------------------------------------
async def analyze_speech(audio_path: str) -> Dict[str, Any]:
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            transcript = recognizer.recognize_google(audio)
            print("Transcript:", transcript)

            # You can apply sentiment/emotion analysis on transcript here (e.g., spaCy, transformers, TextBlob, etc.)
            # For now, just return basic structure.
            return {
                "status": "success",
                "message": "Speech transcription completed.",
                "data": {
                    "transcript": transcript,
                    "emotion_analysis": "Coming soon..."
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

# -------------------------------------------------
# ✅ Combined Video + Audio Emotion Analysis
# -------------------------------------------------
async def analyze_video_audio(video_path: str, audio_path: str) -> Dict[str, Any]:
    try:
        facial_result = await analyze_facial_expression(video_path)
        speech_result = await analyze_speech(audio_path)

        return {
            "status": "success",
            "message": "Combined video and audio analysis completed.",
            "data": {
                "facial_analysis": facial_result.get("data"),
                "speech_analysis": speech_result.get("data")
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": None
        }


# -------------------------------------------------
# ✅ It is used to store interview in database and also return feedback for the candidate
# -------------------------------------------------
async def save_interview_analysis_to_db(db, user_id, interview_id, facial_result, speech_result=None):
    feedback = generate_candidate_feedback(facial_result, speech_result)

    analysis_doc = {
        "user_id": ObjectId(user_id),
        "interview_id": ObjectId(interview_id),
        "facial_analysis": facial_result,
        "speech_analysis": speech_result,
        "ai_feedback": feedback,
        "created_at": datetime.utcnow()
    }

    await db["interview_analysis"].insert_one(analysis_doc)
    return feedback


# -------------------------------------------------
# ✅ It generate feedback for the candidate based on the analysis
# -------------------------------------------------
def generate_candidate_feedback(facial_result, speech_result):
    emotions_summary = facial_result.get("summary", {})
    top_emotions = emotions_summary.get("top_3", [])
    common_emotion = top_emotions[0][0] if top_emotions else "neutral"

    feedback = f"You appeared mostly {common_emotion} during the interview. "

    if speech_result:
        speech_score = speech_result.get("speech_score", 0)
        feedback += f"Your speech clarity score was {speech_score}/10. "

        if speech_score > 7:
            feedback += "You spoke confidently. "
        else:
            feedback += "Try to speak more clearly next time. "

    feedback += "Overall, you performed decently. Practice more for better results."

    return feedback

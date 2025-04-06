import numpy as np
import cv2
import tempfile
import os
import logging
import asyncio
from collections import deque
from datetime import datetime
from bson import ObjectId

from app.database import get_database
from app.services.ai.ai_analysis import analyze_facial_expression
from app.services.ai.speech_analysis import analyze_speech

logger = logging.getLogger(__name__)

MAX_EMOTION_HISTORY = 5
FACIAL_FEEDBACK_BATCH_SIZE = 3


async def process_facial_expression(video_data, interview_id, user_id, websocket, session_id):
    emotion_history = deque(maxlen=MAX_EMOTION_HISTORY)
    batch_counter = 0

    try:
        db = await get_database()

        video_array = np.frombuffer(video_data, np.uint8)
        frame = cv2.imdecode(video_array, cv2.IMREAD_COLOR)

        if frame is None:
            raise ValueError("Invalid video frame received.")

        logger.info(f"[FACIAL] Analyzing expression for user {user_id}")

        emotion = await analyze_facial_expression(frame)
        emotion_history.append(emotion)
        batch_counter += 1

        await db.facial_analysis.insert_one({
            "interview_id": ObjectId(interview_id),
            "user_id": user_id,
            "session_id": session_id,
            "emotion": emotion,
            "timestamp": datetime.utcnow()
        })

        if batch_counter >= FACIAL_FEEDBACK_BATCH_SIZE:
            emotion_summary = {
                "most_common": max(set(emotion_history), key=emotion_history.count),
                "history": list(emotion_history)
            }

            await websocket.send_json({
                "interview_id": interview_id,
                "user_id": user_id,
                "facial_expression_summary": emotion_summary
            })

            batch_counter = 0

        await asyncio.sleep(0.5)

    except Exception as e:
        logger.exception(f"[FACIAL ERROR] User {user_id} | {str(e)}")
        await websocket.send_text(f"Facial Analysis Error: {str(e)}")


async def process_speech(audio_data, interview_id, user_id, websocket, session_id):
    audio_path = None

    try:
        db = await get_database()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_data)
            audio_path = tmp.name

        logger.info(f"[SPEECH] Analyzing speech for {user_id}...")

        result = await analyze_speech(audio_path)

        sentiment_score = result.get("sentiment_score", 0.0)
        sentiment = result.get("sentiment", "unknown")
        transcript = result.get("transcript", "")
        keywords = result.get("keywords", [])

        await db.speech_analysis.insert_one({
            "interview_id": ObjectId(interview_id),
            "user_id": user_id,
            "session_id": session_id,
            "transcript": transcript,
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "keywords": keywords,
            "timestamp": datetime.utcnow()
        })

        await websocket.send_json({
            "interview_id": interview_id,
            "user_id": user_id,
            "speech_analysis": {
                "transcript": transcript,
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "keywords": keywords
            }
        })

    except Exception as e:
        logger.exception(f"[SPEECH ERROR] User {user_id} | {str(e)}")
        await websocket.send_text(f"Speech Analysis Error: {str(e)}")

    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
            logger.debug(f"[CLEANUP] Deleted temp audio file: {audio_path}")

from fastapi import FastAPI, WebSocket, APIRouter, Query, HTTPException
from fastapi import WebSocketDisconnect
import asyncio
import cv2
import numpy as np
from app.services.ai.ai_analysis import (
    analyze_facial_expression,
    analyze_speech
)
from app.services.auth import get_current_user
import logging
import os
import tempfile

app = FastAPI()
router = APIRouter()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

app.include_router(router)


@router.websocket("/ws/{interview_id}")
async def websocket_feedback(
    websocket: WebSocket,
    interview_id: str,
    token: str = Query(...)
):
    # WebSocket API for real-time AI analysis.
    # - Authenticates user with token.
    # - Processes video frames (facial expression analysis).
    # - Analyzes speech.
    # - Sends results to the client.
    try:
        # Authenticate user
        logger.info(
            f"[AUTH] Received WebSocket connection request with token: {token}"
        )
        current_user = await get_current_user(token)
        client_id = current_user["client_id"]
        logger.info(f"[AUTH] User {client_id} authenticated successfully.")

        await websocket.accept()
        logger.info(
            f"[WEBSOCKET] Connection established with {client_id} "
            f"for Interview {interview_id}"
        )

        while True:
            try:
                # Receive video and audio data
                video_data = await websocket.receive_bytes()
                audio_data = await websocket.receive_bytes()
                logger.info(
                    f"[DATA] Received video & audio data from {client_id}"
                )
# Process video & audio simultaneously using asyncio.gather()
                facial_analysis_task = process_facial_expression(
                    video_data, interview_id, client_id, websocket
                )
                speech_analysis_task = process_speech(
                    audio_data, interview_id, client_id, websocket
                )

                await asyncio.gather(
                    facial_analysis_task, speech_analysis_task
                )

            except WebSocketDisconnect:
                logger.warning(
                    f"[WEBSOCKET] Client {client_id} "
                    f"disconnected unexpectedly."
                )
                break

    except HTTPException as e:
        logger.error(f"[ERROR] Authentication failed: {e.detail}")
        await websocket.close(code=403)
    except Exception as e:
        logger.error(f"[ERROR] WebSocket error: {str(e)}")
        await websocket.send_text(f"Error: {str(e)}")
        await websocket.close()
    finally:
        logger.info(f"[WEBSOCKET] Connection closed for {client_id}")


async def process_facial_expression(
    video_data, interview_id, client_id, websocket
):
    # Analyzes facial expressions from the received video data.
    try:
        # Convert video data to OpenCV format
        video_array = np.frombuffer(video_data, np.uint8)
        video_capture = cv2.imdecode(video_array, cv2.IMREAD_COLOR)

        if video_capture is None:
            raise ValueError("Invalid video data received.")

        logger.info(
            f"[FACIAL] Processing facial expressions for {client_id}..."
        )

        # Process each frame (in-memory, no temp file)
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break

            frame_np = np.array(frame)
            emotion = await analyze_facial_expression(frame_np)

            # Send results via WebSocket
            await websocket.send_json({
                "interview_id": interview_id,
                "user_id": client_id,
                "facial_expression": emotion
            })

            await asyncio.sleep(1)  # Control frame processing rate

    except Exception as e:
        logger.error(f"[FACIAL] Error processing facial expression: {e}")
        await websocket.send_text(f"Facial Analysis Error: {str(e)}")


async def process_speech(audio_data, interview_id, client_id, websocket):
    # Analyzes speech from the received audio data.
    try:
        # Save temporary audio file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".wav"
        ) as audio_file:
            audio_file.write(audio_data)
            audio_path = audio_file.name

        logger.info(f"[SPEECH] Processing speech for {client_id}...")

        speech_result = await analyze_speech(audio_path)

        # Send results via WebSocket
        await websocket.send_json({
            "interview_id": interview_id,
            "user_id": client_id,
            "speech_analysis": speech_result
        })

    except Exception as e:
        logger.error(f"[SPEECH] Error processing speech: {e}")
        await websocket.send_text(f"Speech Analysis Error: {str(e)}")
    finally:
        # Cleanup audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logger.debug(f"[CLEANUP] Deleted temp audio file: {audio_path}")

from fastapi import FastAPI, WebSocket, APIRouter, Query, HTTPException
from fastapi import WebSocketDisconnect
import asyncio
import logging
import uuid

from app.services.auth import get_current_user
from app.services.ai.websocket import (
    process_facial_expression,
    process_speech
)

app = FastAPI()
router = APIRouter(prefix="/ws", tags=["WebSocket"])

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

app.include_router(router)


@router.websocket("/{interview_id}")
async def websocket_feedback(
    websocket: WebSocket,
    interview_id: str,
    token: str = Query(...)
):
    try:
        # Authenticate user
        logger.info(f"[AUTH] WebSocket connection request with token: {token}")
        current_user = await get_current_user(token)
        user_id = current_user["client_id"]
        logger.info(f"[AUTH] User {user_id} authenticated.")

        # Accept WebSocket
        await websocket.accept()
        logger.info(f"[WEBSOCKET] Connected: user {user_id}, interview {interview_id}")

        # Generate unique session ID
        session_id = str(uuid.uuid4())
        logger.info(f"[SESSION] New session started: {session_id}")

        while True:
            try:
                # Expect: 1st chunk = video, 2nd chunk = audio
                video_data = await websocket.receive_bytes()
                audio_data = await websocket.receive_bytes()
                logger.info(f"[DATA] Received video/audio from {user_id}")

                await asyncio.gather(
                    process_facial_expression(video_data, interview_id, user_id, websocket, session_id),
                    process_speech(audio_data, interview_id, user_id, websocket, session_id)
                )

            except WebSocketDisconnect:
                logger.warning(f"[DISCONNECT] Client {user_id} disconnected.")
                break

    except HTTPException as e:
        logger.error(f"[AUTH FAIL] {e.detail}")
        await websocket.close(code=403)
    except Exception as e:
        logger.error(f"[ERROR] WebSocket exception: {str(e)}")
        await websocket.send_text(f"Error: {str(e)}")
        await websocket.close()
    finally:
        logger.info(f"[WEBSOCKET] Closed for user {user_id}")

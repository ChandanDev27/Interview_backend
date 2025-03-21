import asyncio
import logging
from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from app.services.ai.ai_analysis import analyze_video_audio

router = APIRouter()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.websocket("/ws/{interview_id}")
async def websocket_feedback(websocket: WebSocket, interview_id: str):
    """
    WebSocket connection for real-time AI feedback.
    Receives video & audio paths, processes them, and returns feedback.
    """
    await websocket.accept()
    logger.info(f"✅ WebSocket connected: {interview_id}")

    try:
        while True:
            # ✅ Receive data safely
            data = await websocket.receive_text()
            if "," not in data:
                logger.warning("⚠️ Invalid input format")
                await websocket.send_json({
                    "error": "Invalid format. Expected 'video_path,audio_path'"
                })
                continue

            video_path, audio_path = data.split(",")

            # ✅ Validate input paths
            if not video_path.endswith(".mp4") or \
               not audio_path.endswith(".wav"):
                logger.warning("🚨 Invalid file types received")
                await websocket.send_json({
                    "error": "Invalid file types. Expected .mp4 and .wav"
                })
                continue

            # ✅ Process AI analysis asynchronously
            feedback = await asyncio.to_thread(
                analyze_video_audio, video_path, audio_path
            )

            # ✅ Send response
            await websocket.send_json(feedback)

    except WebSocketDisconnect:
        logger.info(f"❌ WebSocket disconnected: {interview_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {str(e)}")
        await websocket.send_json({"error": "Internal Server Error"})
    finally:
        await websocket.close()
        logger.info(f"🔒 WebSocket closed: {interview_id}")

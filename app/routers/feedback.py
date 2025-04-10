import asyncio
import logging
from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from app.services.ai.ai_analysis import analyze_video_audio

router = APIRouter(tags=["Real-time Feedback"])

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("feedback_ws")


@router.websocket("/ws/{interview_id}")
async def websocket_feedback(websocket: WebSocket, interview_id: str):
    """
    WebSocket endpoint for real-time AI feedback.
    Receives 'video_path,audio_path' and returns facial & speech analysis.
    """
    await websocket.accept()
    logger.info(f"✅ WebSocket connected for Interview ID: {interview_id}")

    try:
        while True:
            data = await websocket.receive_text()

            # Validate format
            if "," not in data:
                logger.warning("⚠️ Invalid input format")
                await websocket.send_json({
                    "error": "Invalid format. Use: 'video_path,audio_path'"
                })
                continue

            video_path, audio_path = map(str.strip, data.split(",", 1))

            # Validate extensions
            if not video_path.endswith(".mp4") or not audio_path.endswith(".wav"):
                logger.warning("🚨 Unsupported file types")
                await websocket.send_json({
                    "error": "Invalid file types. Expected '.mp4' and '.wav'"
                })
                continue

            logger.info(f"🧠 Analyzing: {video_path} + {audio_path}")
            try:
                feedback = await analyze_video_audio(video_path, audio_path)

                await websocket.send_json({
                    "interview_id": interview_id,
                    "status": "success",
                    "feedback": feedback
                })
            except Exception as analysis_error:
                logger.error(f"❌ AI analysis failed: {str(analysis_error)}")
                await websocket.send_json({
                    "error": "AI analysis failed. Please try again."
                })

    except WebSocketDisconnect:
        logger.info(f"❌ WebSocket disconnected: {interview_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {str(e)}")
        await websocket.send_json({"error": "Internal Server Error"})
    finally:
        await websocket.close()
        logger.info(f"🔒 WebSocket closed: {interview_id}")

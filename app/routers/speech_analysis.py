from fastapi import APIRouter, File, UploadFile, HTTPException
import shutil
import tempfile
import os
import logging
from pydub import AudioSegment  # Convert MP3 to WAV
from app.services.ai.ai_analysis import analyze_speech

router = APIRouter(prefix="/api", tags=["Speech Analysis"])
logger = logging.getLogger(__name__)


@router.post("/analyze_speech")
async def analyze_speech_api(file: UploadFile = File(...)):
    # API Endpoint to analyze speech from an uploaded audio file.
    # Supports both MP3 and WAV formats.
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    # Validate file format
    if not file.filename.lower().endswith((".wav", ".mp3")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Upload a WAV or MP3 file."
        )

    try:
        with tempfile.NamedTemporaryFile(
                delete=False, suffix=".wav") as temp_wav:
            temp_wav_path = temp_wav.name

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3" if file.filename.endswith(".mp3") else ".wav"
        ) as temp_audio:
            temp_audio_path = temp_audio.name

            # Read file in chunks to avoid memory overload
            with open(temp_audio_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        # Convert MP3 to WAV if necessary
        if file.filename.endswith(".mp3"):
            audio = AudioSegment.from_file(temp_audio_path, format="mp3")
            audio.export(temp_wav_path, format="wav")
        else:
            temp_wav_path = temp_audio_path

        # Run AI-based speech analysis
        speech_result = await analyze_speech(temp_wav_path)

        return speech_result

    except Exception as e:
        logger.error(f"❌ Error processing speech file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        # Clean up temporary files
        for path in [temp_audio_path, temp_wav_path]:
            if os.path.exists(path):
                os.remove(path)

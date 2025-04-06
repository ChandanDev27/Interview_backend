from fastapi import APIRouter, File, UploadFile, HTTPException, status
import shutil
import tempfile
import os
import logging
from pydub import AudioSegment
from app.services.ai.speech_analysis import analyze_speech

router = APIRouter(prefix="/api/speech", tags=["Speech Analysis"])
logger = logging.getLogger(__name__)


@router.post("/analyze", summary="Analyze uploaded speech audio file")
async def analyze_speech_api(file: UploadFile = File(...)):
    """
    Analyze an uploaded audio file (WAV/MP3) to generate:
    - Transcript
    - Sentiment analysis
    - Extracted keywords

    Returns structured AI analysis.
    """
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded.")

    if not file.filename.lower().endswith((".wav", ".mp3")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .wav and .mp3 audio formats are supported."
        )

    temp_audio_path = ""
    temp_wav_path = ""

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            temp_wav_path = temp_wav.name

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3" if file.filename.endswith(".mp3") else ".wav"
        ) as temp_audio:
            temp_audio_path = temp_audio.name
            shutil.copyfileobj(file.file, temp_audio)

        # Convert MP3 to WAV if needed
        if file.filename.lower().endswith(".mp3"):
            audio = AudioSegment.from_file(temp_audio_path, format="mp3")
            audio.export(temp_wav_path, format="wav")
        else:
            temp_wav_path = temp_audio_path

        logger.info(f"🎤 Analyzing speech from: {file.filename}")
        result = analyze_speech(temp_wav_path)
        logger.info(f"✅ Analysis complete: {result}")
        return result

    except Exception as e:
        logger.exception(f"❌ Error analyzing speech: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Speech analysis failed.")

    finally:
        for path in [temp_audio_path, temp_wav_path]:
            if os.path.exists(path):
                os.remove(path)

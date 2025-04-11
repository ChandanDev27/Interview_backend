from passlib.context import CryptContext
from pathlib import Path
import re
import ffmpeg
import os
import tempfile
import subprocess
import cv2

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class WeakPasswordError(Exception):
    pass


def is_password_strong(password: str) -> bool:
    return (
        len(password) >= 8 and
        bool(re.search(r"\d", password)) and
        bool(re.search(r"[a-z]", password)) and
        bool(re.search(r"[A-Z]", password)) and
        bool(re.search(r"[@$!%*?&]", password))
    )


def hash_password(password: str) -> str:
    # Hash a password after checking strength.
    if not is_password_strong(password):
        raise WeakPasswordError("Password is too weak. It must be at least 8 characters long and include digits, uppercase, lowercase, and special characters.")
    return pwd_context.hash(password)



def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)

def extract_audio_from_video(video_path: str) -> str:
    try:
        video_file = Path(video_path).resolve()
        if not video_file.exists():
            raise FileNotFoundError(f"Video file does not exist at: {video_file}")

        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        audio_path = temp_audio.name
        temp_audio.close()

        ffmpeg_path = r"C:\ffmpeg\ffmpeg.exe"  # Use full build with Opus/WebM support

        command = [
            ffmpeg_path,
            "-y",
            "-i", str(video_file),
            "-vn",  # skip video
            "-acodec", "pcm_s16le",
            "-ac", "1",
            "-ar", "16000",
            "-f", "wav",
            audio_path
        ]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

        return audio_path

    except Exception as e:
        raise RuntimeError(f"Audio extraction failed: {str(e)}")


def get_video_duration(video_path: str) -> float:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 0.0

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()

    if fps == 0:
        return 0.0

    return frame_count / fps

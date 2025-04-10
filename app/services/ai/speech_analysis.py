import os
import speech_recognition as sr
from typing import Dict, Any
import spacy
from textblob import TextBlob
from fastapi.concurrency import run_in_threadpool
from collections import Counter
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import librosa
import numpy as np
import ffmpeg

# Set up logger
logger = logging.getLogger(__name__)
nlp = spacy.load("en_core_web_sm")
analyzer = SentimentIntensityAnalyzer()

# Custom stopwords for keyword extraction
custom_stopwords = {"problem", "solution", "example", "study"}  # Adjust as needed

# Define default pitch thresholds, which can be tuned based on speaker characteristics
DEFAULT_PITCH_THRESHOLDS = {
    "low": 100,        # Low pitch for deeper voices
    "moderate": 250,   # Moderate pitch for normal voices
    "high": 350        # High pitch for higher-pitched voices
}

def extract_audio_from_video(video_path: str) -> str:
    """Extract audio from the video file using ffmpeg."""
    try:
        audio_path = f"{os.path.splitext(video_path)[0]}.wav"
        
        # Extract audio using ffmpeg
        ffmpeg.input(video_path).output(audio_path).run(overwrite_output=True)
        
        logger.info(f"🎧 Audio successfully extracted to: {audio_path}")
        return audio_path
    except Exception as e:
        logger.error(f"❌ Failed to extract audio from {video_path}: {e}")
        raise e


def calculate_speech_clarity(audio_path: str) -> float:
    """Calculate a speech clarity score based on the signal-to-noise ratio (SNR)."""
    try:
        # Load the audio file
        y, sr_librosa = librosa.load(audio_path, sr=None)  # Use 'sr_librosa' to avoid conflict with 'sr' from speech_recognition

        # Calculate the root mean square (RMS) energy
        rms = librosa.feature.rms(y=y)[0]

        # Estimate the signal-to-noise ratio (SNR)
        signal_energy = np.mean(rms ** 2)
        noise_energy = np.var(rms)
        snr = 10 * np.log10(signal_energy / (noise_energy + 1e-10))  # Avoid division by zero

        # Normalize the SNR to a score between 0 and 10
        clarity_score = max(0, min(10, snr / 10))  # Scale SNR to a 0-10 range
        return round(clarity_score, 2)
    except Exception as e:
        logger.error(f"❌ Error calculating speech clarity: {e}")
        return 0.0  # Default to 0 if calculation fails

def calculate_speech_rate(transcript: str, audio_duration: float) -> float:
    """Calculate the speech rate as words per second."""
    try:
        word_count = len(transcript.split())
        return round(word_count / audio_duration, 2) if audio_duration > 0 else 0.0
    except Exception as e:
        logger.error(f"❌ Error calculating speech rate: {e}")
        return 0.0

def analyze_speech(audio_path: str) -> Dict[str, Any]:
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            transcript = recognizer.recognize_google(audio)
            logger.info(f"🎙️ Transcript: {transcript}")

            # Calculate the speech clarity score
            speech_score = calculate_speech_clarity(audio_path)

            # Calculate the audio duration using librosa (avoiding 'sr' conflict)
            try:
                y, sr_librosa = librosa.load(audio_path, sr=None)  # Use 'sr_librosa' as the sample rate
            except Exception as e:
                logger.error(f"❌ Error loading audio file for duration calculation: {e}")
                y, sr_librosa = None, 22050  # Fallback sample rate

            if y is not None:
                audio_duration = librosa.get_duration(y=y, sr=sr_librosa)
            else:
                audio_duration = 0.0  # Default duration if loading fails

            # Calculate the speech rate
            speech_rate = calculate_speech_rate(transcript, audio_duration)

            # Return the structured result
            return {
                "status": "success",
                "message": "Speech transcription completed.",
                "data": {
                    "transcript": transcript,
                    "speech_score": speech_score,
                    "speech_rate": speech_rate,
                    "intonation": "neutral",  # Placeholder, replace with intonation analysis if needed
                    "overall_sentiment": "neutral"  # Placeholder, replace with sentiment analysis if needed
                }
            }

    except sr.UnknownValueError:
        logger.error("❌ Could not understand the audio.")
        return {
            "status": "error",
            "message": "Could not understand audio",
            "data": {
                "transcript": "",
                "intonation": "neutral",  # Default to "neutral"
                "speech_rate": 0.0
            }
        }
    except Exception as e:
        logger.error(f"❌ Error during speech analysis: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": {
                "transcript": "",
                "intonation": "neutral",  # Default to "neutral"
                "speech_rate": 0.0
            }
        }


def analyze_intonation(audio_path: str, pitch_thresholds: dict = None) -> str:
    try:
        # Use default thresholds if none are provided
        if pitch_thresholds is None:
            pitch_thresholds = DEFAULT_PITCH_THRESHOLDS

        # Validate thresholds
        if not (pitch_thresholds["low"] < pitch_thresholds["moderate"] < pitch_thresholds["high"]):
            logger.warning(f"⚠️ Invalid pitch thresholds provided. Falling back to default thresholds.")
            pitch_thresholds = DEFAULT_PITCH_THRESHOLDS

        # Load the audio file
        y, sr = librosa.load(audio_path, sr=None)

        # Extract pitch (F0) using librosa's `pyin` method
        pitches, voiced_flags, _ = librosa.pyin(y, fmin=50, fmax=500, sr=sr)

        # Filter out unvoiced frames
        voiced_pitches = pitches[voiced_flags]

        # Check if pitch is found
        if len(voiced_pitches) == 0:
            logger.error("❌ No significant pitch found in the audio file.")  # Log error if no pitch is found
            return "neutral"  # Default to "neutral"
        else:
            pitch = np.mean(voiced_pitches)
            return classify_pitch(pitch, pitch_thresholds)

    except Exception as e:
        logger.error(f"❌ Error during intonation analysis: {e}")
        return "neutral"  # Default to "neutral"

def classify_pitch(pitch: float, pitch_thresholds: dict) -> str:
    """Classify the pitch into low, moderate, or high based on thresholds."""
    if pitch < pitch_thresholds["low"]:
        return "low"
    elif pitch < pitch_thresholds["moderate"]:
        return "moderate"
    else:
        return "high"


def _analyze_speech_blocking(audio_path: str, language: str = "en-US", top_n_keywords: int = 10, pitch_thresholds: dict = None):
    """
    Analyze the speech in the given audio file and return a structured analysis.

    Args:
        audio_path (str): Path to the audio file.
        language (str): Language code for speech recognition (default: "en-US").
        top_n_keywords (int): Number of top keywords to extract (default: 10).
        pitch_thresholds (dict): Dictionary of pitch thresholds for intonation analysis.

    Returns:
        dict: A dictionary containing the transcript, sentiment, and keywords.
    """
    # Initialize recognizer
    if not os.path.exists(audio_path):
        logger.error(f"❌ Audio file does not exist: {audio_path}")
        return {
            "detail": "Audio file does not exist.",
            "transcript": "",
            "sentiment": "neutral"  # Default to "neutral"
        }

    # Initialize recognizer and load model
    recognizer = sr.Recognizer()

    # Log audio file processing
    logger.info(f"🎧 Processing audio file: {audio_path}")

    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)

    try:
        logger.info("🔄 Recognizing speech from audio...")
        transcript = recognizer.recognize_google(audio, language=language).strip()

        # Check for empty transcript
        if not transcript:
            logger.warning("⚠️ Received an empty transcript.")
            return {
                "detail": "No speech detected.",
                "transcript": "",
                "sentiment": "neutral"  # Default to "neutral"
            }

        logger.info(f"🎙️ Transcript recognized: {transcript}")
    except sr.UnknownValueError:
        logger.error(f"❌ Could not understand audio from {audio_path}.")
        return {
            "detail": "Could not understand audio.",
            "transcript": "",
            "sentiment": "neutral"  # Default to "neutral"
        }
    except sr.RequestError as e:
        logger.error(f"❌ API error while processing {audio_path}: {e}")
        return {
            "detail": "Speech recognition API unavailable.",
            "transcript": "",
            "sentiment": "neutral"  # Default to "neutral"
        }

    # Sentiment and keyword analysis
    logger.info("📊 Analyzing sentiment and extracting keywords from transcript...")
    doc = nlp(transcript)
    blob = TextBlob(transcript)

    # VADER sentiment analysis
    sentiment_scores = analyzer.polarity_scores(transcript)
    logger.debug(f"Sentiment scores for transcript: {sentiment_scores}")

    # If compound score is None, set a fallback value
    if sentiment_scores['compound'] is None:
        sentiment_scores['compound'] = 0.0  # Fallback value to ensure it doesn't break

    sentiment_label = "positive" if sentiment_scores['compound'] > 0.1 else "negative" if sentiment_scores['compound'] < -0.1 else "neutral"

    sentiment_trend = [
        {"sentence": str(sentence), "sentiment": TextBlob(str(sentence)).sentiment.polarity}
        for sentence in blob.sentences
    ]

    # Intonation analysis using librosa with dynamic thresholds
    intonation = analyze_intonation(audio_path, pitch_thresholds)

    # Keyword extraction, excluding custom stopwords
    all_keywords = [token.text.lower() for token in doc if token.is_alpha and token.text.lower() not in custom_stopwords]
    keyword_freq = Counter(all_keywords)
    top_keywords = [word for word, _ in keyword_freq.most_common(top_n_keywords)]

    logger.info(f"📊 Sentiment: {sentiment_label} (Score: {sentiment_scores['compound']})")
    logger.info(f"🔑 Extracted keywords: {top_keywords}")

    return {
        "transcript": transcript,
        "overall_sentiment": sentiment_label,
        "sentence_sentiments": sentiment_trend,
        "intonation": intonation,
        "keywords": top_keywords,
        "summary": {
            "overall_sentiment": sentiment_label,
            "intonation": intonation
        }
    }

import speech_recognition as sr
import spacy
from textblob import TextBlob
from fastapi.concurrency import run_in_threadpool
from collections import Counter
import logging

logger = logging.getLogger(__name__)
nlp = spacy.load("en_core_web_sm")


async def analyze_speech(audio_path: str, language: str = "en-US", top_n_keywords: int = 10):
    """
    Asynchronously analyzes speech: transcript, sentiment, and keywords.
    
    Args:
        audio_path (str): Path to the audio file.
        language (str): Language code for recognition (default is "en-US").
        top_n_keywords (int): Number of top frequent keywords to return.

    Returns:
        dict: Analysis including transcript, sentiment score, label, keywords.
    """
    try:
        return await run_in_threadpool(_analyze_speech_blocking, audio_path, language, top_n_keywords)

    except Exception as e:
        logger.exception(f"❌ Unhandled error during speech analysis: {str(e)}")
        return {
            "detail": "Speech analysis failed.",
            "error": str(e),
            "sentiment": "unknown",
            "transcript": ""
        }


def _analyze_speech_blocking(audio_path: str, language: str = "en-US", top_n_keywords: int = 10):
    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)

    try:
        transcript = recognizer.recognize_google(audio, language=language).strip()
        logger.info(f"🎙️ Transcript: {transcript}")
    except sr.UnknownValueError:
        logger.error("❌ Could not understand the audio.")
        return {
            "detail": "Could not understand audio.",
            "transcript": "",
            "sentiment": "unknown"
        }
    except sr.RequestError as e:
        logger.error(f"❌ API error: {e}")
        return {
            "detail": "Speech recognition API unavailable.",
            "transcript": "",
            "sentiment": "unknown"
        }

    # NLP & Sentiment Analysis
    doc = nlp(transcript)
    sentiment = TextBlob(transcript).sentiment
    sentiment_score = round(sentiment.polarity, 2)
    sentiment_label = (
        "positive" if sentiment_score > 0.1 else
        "negative" if sentiment_score < -0.1 else
        "neutral"
    )

    logger.info(f"📊 Sentiment: {sentiment_label} ({sentiment_score})")

    # Keyword Extraction (top-N most frequent)
    all_keywords = [token.text.lower() for token in doc if token.is_alpha and not token.is_stop]
    keyword_freq = Counter(all_keywords)
    top_keywords = [word for word, _ in keyword_freq.most_common(top_n_keywords)]

    logger.info(f"🔑 Keywords: {top_keywords}")

    return {
        "transcript": transcript,
        "sentiment_score": sentiment_score,
        "sentiment": sentiment_label,
        "keywords": top_keywords
    }

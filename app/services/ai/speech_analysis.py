# speech_analysis.py
import speech_recognition as sr
import spacy
from textblob import TextBlob
from fastapi.concurrency import run_in_threadpool
from collections import Counter
import logging

logger = logging.getLogger(__name__)
nlp = spacy.load("en_core_web_sm")

async def analyze_speech(audio_path: str, language: str = "en-US", top_n_keywords: int = 10):
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

    doc = nlp(transcript)
    blob = TextBlob(transcript)
    sentiment_score = round(blob.sentiment.polarity, 2)
    sentiment_label = (
        "positive" if sentiment_score > 0.1 else
        "negative" if sentiment_score < -0.1 else
        "neutral"
    )

    sentiment_trend = [
        {"sentence": str(sentence), "sentiment": TextBlob(str(sentence)).sentiment.polarity}
        for sentence in blob.sentences
    ]

    intonation = "moderate"  # Placeholder

    all_keywords = [token.text.lower() for token in doc if token.is_alpha and not token.is_stop]
    keyword_freq = Counter(all_keywords)
    top_keywords = [word for word, _ in keyword_freq.most_common(top_n_keywords)]

    logger.info(f"📊 Sentiment: {sentiment_label} ({sentiment_score})")
    logger.info(f"🔑 Keywords: {top_keywords}")

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

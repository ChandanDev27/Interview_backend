import speech_recognition as sr
import spacy

nlp = spacy.load("en_core_web_sm")


def analyze_speech(audio_path: str):
    r = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = r.record(source)
        transcript = r.recognize_google(audio)
    doc = nlp(transcript)
    sentiment = (
        doc._.polarity
        if hasattr(doc._, "polarity")
        else "Sentiment analysis not available"
    )
    return {"transcript": transcript, "sentiment": sentiment}

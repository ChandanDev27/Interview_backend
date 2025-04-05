import asyncio
import cv2
import numpy as np
import soundfile as sf
import librosa
import speech_recognition as sr
import spacy
from fer import FER
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Load Spacy NLP model
nlp = spacy.load("en_core_web_sm")

# Initialize FER detector and Sentiment Analyzer
fer_detector = FER()
analyzer = SentimentIntensityAnalyzer()


async def analyze_facial_expression(video_path: str):
    emotions_data = []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap.release()
        return {"error": "Failed to open video file"}

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_interval = max(1, fps // 2)  # Analyze every half second
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                emotions = fer_detector.detect_emotions(frame_rgb)
                if emotions:
                    top_emotion = max(
                        emotions[0]['emotions'],
                        key=emotions[0]['emotions'].get
                    )
                    emotions_data.append({
                        "time": frame_count // fps,
                        "emotion": top_emotion
                    })
            except Exception as e:
                print(f"[Facial Analysis] Frame error: {str(e)}")

        frame_count += 1

    cap.release()
    return {"framewise_emotions": emotions_data}


async def analyze_speech(audio_path: str):
    r = sr.Recognizer()

    try:
        y, sr_rate = librosa.load(audio_path, sr=None)
    except Exception:
        return {"error": "Failed to load audio."}

    if len(y) == 0:
        return {"error": "Empty or unreadable audio file."}

    y = librosa.effects.preemphasis(y, coef=0.97)
    audio_path_cleaned = audio_path.rsplit(".", 1)[0] + "_cleaned.wav"

    try:
        sf.write(audio_path_cleaned, y, sr_rate, format="WAV", subtype="PCM_16")

        with sr.AudioFile(audio_path_cleaned) as source:
            audio = r.record(source)

        try:
            transcript = r.recognize_google(audio)
        except sr.UnknownValueError:
            return {"error": "Could not understand the audio."}
        except sr.RequestError:
            return {"error": "Speech recognition API unavailable."}

    except Exception as e:
        return {"error": f"Speech processing failed: {str(e)}"}

    doc = nlp(transcript)
    sentiment_trend = []
    for sentence in doc.sents:
        score = analyzer.polarity_scores(sentence.text)["compound"]
        sentiment = (
            "Positive" if score > 0.05 else
            "Negative" if score < -0.05 else
            "Neutral"
        )
        sentiment_trend.append({
            "sentence": sentence.text,
            "sentiment": sentiment
        })

    pitches, magnitudes = librosa.piptrack(y=y, sr=sr_rate)
    pitch_values = pitches[magnitudes > np.median(magnitudes)]
    avg_pitch = np.mean(pitch_values) if pitch_values.size > 0 else 150

    intonation = "Calm"
    if avg_pitch > 250:
        intonation = "Excited"
    elif avg_pitch < 120:
        intonation = "Monotone"
    elif 120 <= avg_pitch <= 180:
        intonation = "Confident"

    return {
        "transcript": transcript,
        "sentence_sentiments": sentiment_trend,
        "intonation": intonation
    }


async def analyze_facial_expression_frame(file):
    contents = await file.read()
    np_arr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    emotions = fer_detector.detect_emotions(frame)
    if emotions:
        top_emotion = max(emotions[0]['emotions'], key=emotions[0]['emotions'].get)
        return {"emotion": top_emotion}
    return {"emotion": "No face detected"}


async def analyze_video_audio(video_path: str, audio_path: str):
    try:
        facial_task = analyze_facial_expression(video_path)
        speech_task = analyze_speech(audio_path)
        facial_result, speech_result = await asyncio.gather(
            facial_task,
            speech_task
        )
        return {
            "facial_expression": facial_result,
            "speech_analysis": speech_result
        }
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

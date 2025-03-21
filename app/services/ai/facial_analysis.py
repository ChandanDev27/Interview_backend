from deepface import DeepFace


def analyze_facial_expression(video_path: str):
    try:
        emotions = DeepFace.analyze(video_path, actions=["emotion"])
        return {"emotions": emotions}
    except Exception as e:
        return {"error": str(e)}

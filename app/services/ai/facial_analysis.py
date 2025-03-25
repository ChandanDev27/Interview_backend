from deepface import DeepFace


def analyze_facial_expression(video_path: str):
    try:
        emotions = DeepFace.analyze(video_path, actions=["emotion"])
        if not emotions:
            raise ValueError("No emotions detected in the video.")
        return {"emotions": emotions}
    except Exception as e:
        return {"error": f"Error analyzing facial expression: {str(e)}"}

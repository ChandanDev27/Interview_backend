# import pytest

from fastapi.testclient import TestClient
from app.routers.facial_analysis import router

client = TestClient(router)


def test_analyze_facial_valid_file():

    with open("path/to/valid_video.mp4", "rb") as video_file:
        response = client.post("/api/analyze_facial", files={"file": video_file})
    assert response.status_code == 200
    assert "facial_expression" in response.json()


def test_analyze_facial_invalid_file_type():

    with open("path/to/invalid_video.txt", "rb") as video_file:
        response = client.post("/api/analyze_facial", files={"file": video_file})
    assert response.status_code == 400
    assert response.json()["detail"] == "Only MP4 video files are allowed"


def test_analyze_facial_corrupted_file():

    with open("path/to/corrupted_video.mp4", "rb") as video_file:
        response = client.post("/api/analyze_facial", files={"file": video_file})
    assert response.status_code == 500
    assert "error" in response.json()

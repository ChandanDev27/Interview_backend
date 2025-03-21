from ..database import db
from datetime import datetime
from app.schemas.interview import InterviewModel  # Assuming you have a schema


async def create_interview(user_id: str, candidate_name: str, questions: list):
    try:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("Invalid user_id")

        if not isinstance(candidate_name, str) or not candidate_name.strip():
            raise ValueError("Invalid candidate_name")

        if not isinstance(questions, list) or not questions:
            raise ValueError("Questions must be a non-empty list")

        new_interview = InterviewModel(
            user_id=user_id,
            candidate_name=candidate_name,
            questions=questions,
            responses=[],
            feedback=None,
            status="pending",
            created_at=datetime.utcnow()
        ).dict()

        result = await db["interviews"].insert_one(new_interview)
        return str(result.inserted_id)

    except Exception as e:
        print(f"Error creating interview: {e}")
        return None


async def get_interviews_by_user(user_id: str):
    try:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("Invalid user_id")

        interviews = await db["interviews"].find({"user_id": user_id}).to_list(100)

        # Convert ObjectId to string for response
        for interview in interviews:
            interview["id"] = str(interview["_id"])
            del interview["_id"]  # Remove MongoDB ObjectId field

        return interviews

    except Exception as e:
        print(f"Error fetching interviews: {e}")
        return []

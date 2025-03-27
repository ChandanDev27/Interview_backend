from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
import logging
import asyncio
from app.database import get_database  # Import the get_database function

from app.models.candidate_answers import CandidateAnswer, CandidateAnswerDB

router = APIRouter(prefix="/candidate_answers", tags=["Candidate Answers"])


async def get_answers_collection():
    db = await get_database()  # Ensure the database is connected
    return db.get_collection("candidate_answers")


# ✅ Ensure index for fast lookups


async def create_indexes():
    answers_collection = await get_answers_collection()  # Get the collection
# Get the collection
    await answers_collection.create_index(

        [("candidate_id", 1), ("question_id", 1)], unique=True
    )

# Call the function to create indexes


asyncio.create_task(create_indexes())

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/", response_model=CandidateAnswerDB)
async def store_answer(answer: CandidateAnswer):
    answers_collection = await get_answers_collection()  # Get the collection here
    """
    Stores a candidate's answer in MongoDB.
    Prevents duplicate answers for the same question.
    """
    try:
        # ✅ Check if the candidate has already answered
        existing_answer = await answers_collection.find_one({
            "candidate_id": answer.candidate_id,
            "question_id": answer.question_id
        })
        if existing_answer:
            logger.warning(
                f"⚠️ Duplicate answer attempt: {answer.candidate_id} - "
                f"{answer.question_id}"
            )
            raise HTTPException(
                status_code=400,
                detail="Candidate has already answered this question"
            )

        # ✅ Convert to dictionary & add MongoDB `_id`
        answer_dict = answer.model_dump()
        answer_dict["_id"] = ObjectId()  # MongoDB ID
        answer_dict["created_at"] = datetime.utcnow()

        # ✅ Insert into DB
        result = await answers_collection.insert_one(answer_dict)

        if result.inserted_id:
            logger.info(
                f"✅ Answer stored: {answer.candidate_id} - "
                f"{answer.question_id}"
            )
            return CandidateAnswerDB(**answer_dict, id=str(result.inserted_id))

        raise HTTPException(status_code=500, detail="Failed to store answer")

    except Exception as e:
        logger.exception(f"❌ Error storing answer: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

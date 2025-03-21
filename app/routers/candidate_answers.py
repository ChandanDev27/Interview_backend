from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging
from app.database import database
from app.models.candidate_answers import CandidateAnswer, CandidateAnswerDB

router = APIRouter(prefix="/candidate_answers", tags=["Candidate Answers"])
answers_collection = database.get_collection("candidate_answers")

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store candidate's answer


@router.post("/", response_model=CandidateAnswerDB)
async def store_answer(answer: CandidateAnswer):
    existing_answer = await answers_collection.find_one({
        "candidate_id": answer.candidate_id,
        "question_id": answer.question_id
    })

    if existing_answer:
        logger.warning(
            f"⚠️ Candidate {answer.candidate_id} has already answered "
            f"question {answer.question_id}"
        )
        raise HTTPException(
            status_code=400,
            detail="Candidate has already answered this question"
        )

    answer_dict = answer.model_dump()
    answer_dict["created_at"] = datetime.utcnow()

    # Insert answer into the database
    result = await answers_collection.insert_one(answer_dict)
    if result.inserted_id:
        logger.info(
            f"✅ Answer stored successfully for candidate {answer.candidate_id}"
        )
        return CandidateAnswerDB(**answer_dict, id=str(result.inserted_id))

    logger.error(
        f"❌ Failed to store answer for candidate {answer.candidate_id}"
    )
    raise HTTPException(status_code=500, detail="Failed to store answer")

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging
from app.database import get_database
from app.models.candidate_answers import CandidateAnswer, CandidateAnswerDB

router = APIRouter(prefix="/candidate_answers", tags=["Candidate Answers"])
async def get_answers_collection():
    db = await get_database()  # Ensure connection
    return db.get_collection("candidate_answers")

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store candidate's answer
@router.post("/", response_model=CandidateAnswerDB)
async def store_answer(answer: CandidateAnswer):
    # Check if the candidate has already answered this question
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

    # Prepare the answer for insertion
    answer_dict = answer.model_dump()
    answer_dict["created_at"] = datetime.utcnow()

    # Insert answer into the database
    try:
        result = await answers_collection.insert_one(answer_dict)
        
        # If insert is successful, return the answer
        if result.inserted_id:
            logger.info(
                f"✅ Answer stored successfully for candidate {answer.candidate_id}, "
                f"question {answer.question_id}"
            )
            return CandidateAnswerDB(**answer_dict, id=str(result.inserted_id))
        else:
            raise Exception("Insert operation failed.")
    
    # Catch any exceptions during database insertion
    except Exception as e:
        logger.error(
            f"❌ Failed to store answer for candidate {answer.candidate_id}, "
            f"question {answer.question_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Failed to store answer")

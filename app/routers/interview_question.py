from fastapi import APIRouter, Depends, HTTPException, status, Query
import logging
from typing import List, Optional
from app.schemas.interview_question import QuestionModel
from app.services.interview_question import QuestionService
from app.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/questions", tags=["Questions"])


logger = logging.getLogger(__name__)
logger.info("Seeding questions...")


@router.get("/", response_model=list[QuestionModel])
async def get_questions(
    db: AsyncIOMotorDatabase = Depends(get_database),
    experience_level: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50
):
    return await QuestionService.get_questions(
        db=db,
        experience_level=experience_level,
        category=category,
        keyword=keyword,
        skip=skip,
        limit=limit
    )


@router.get("/experience/{experience_level}", response_model=List[QuestionModel])
async def get_questions(
    experience_level: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get interview questions by experience level: fresher, experienced, or both.
    """
    if experience_level not in {"fresher", "experienced", "both"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid experience level. Choose from 'fresher', 'experienced', or 'both'."
        )
    
    questions = await QuestionService.get_questions(db, experience_level=experience_level)
    return questions

@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_interview_questions(db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Seed the database with predefined interview questions.
    """
    await QuestionService.seed_questions(db)
    return {"message": "Questions seeding completed (or skipped if already exists)."}

@router.post("/indexes")
async def create_question_indexes(db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Create indexes on question collection for optimized querying.
    """
    await QuestionService.create_indexes(db)
    return {"message": "Indexes created successfully."}

@router.get("/search", response_model=List[QuestionModel])
async def search_questions(
    category: str = None,
    keyword: str = None,
    difficulty: str = None,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await QuestionService.search_questions(db, category, keyword, difficulty)


from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from bson import ObjectId, errors
from app.database import MongoDBManager, get_database, mongodb_manager
from app.routers import (
    auth, user, interview, facial_analysis, feedback, websocket, health,
    speech_analysis, interview_question, ai_analysis, candidate_answers
)
from app.routers.websocket import router as websocket_router
from app.schemas.user import User
from app.services.interview_question import QuestionService
from app.config import settings, logger
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="Interview Genie Backend", version="1.0")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
media_path = os.path.join(BASE_DIR, "../media")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.include_router(auth.router, tags=["Authentication"])
app.include_router(user.router)
app.include_router(interview.router)
app.include_router(websocket_router, prefix="/api")
app.include_router(facial_analysis.router)
app.include_router(speech_analysis.router)
app.include_router(interview_question.router)
app.include_router(ai_analysis.router)
app.include_router(candidate_answers.router)
app.include_router(feedback.router)
app.include_router(health.router)
app.include_router(websocket.router, prefix="/api")
app.mount("/media", StaticFiles(directory="media"), name="media")

# Initialize MongoDB
mongo_manager = MongoDBManager(
    uri=settings.MONGO_URI,
    db_name=settings.MONGO_DB_NAME,
    settings=settings
)


async def ensure_indexes():
    db = await get_database()
    users_collection = db["users"]
    await users_collection.create_index([("email", 1)], unique=True)

    interviews_collection = db["interviews"]
    await interviews_collection.create_index([("user_id", 1)])


# FastAPI Lifecycle Events
@app.on_event("startup")
async def startup_event():
    await mongo_manager.connect()
    await ensure_indexes()
    db = mongodb_manager.db
    await QuestionService.seed_questions(db)

@app.on_event("shutdown")
async def shutdown_event():
    await mongo_manager.close()
    await ensure_indexes()

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"message": "An internal server error occurred"})

# Rate Limit Exception Handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"message": "Too many requests! Please try again later."}
    )

# Serialize MongoDB User Document
def serialize_user(user):
    return {
        "id": str(user["_id"]),
        "name": user.get("name", "Anonymous"),
        "email": user.get("email", "N/A"),
        "imageUrl": user.get("imageUrl", ""),
        "createdAt": user.get("createdAt", datetime.utcnow()),
        "updatedAt": user.get("updatedAt", datetime.utcnow()),
    }

# Store User API
@app.post("/auth/store-user/")
async def store_user(user: User, db=Depends(get_database)):
    try:
        users_collection = db["users"]
        existing_user = await users_collection.find_one({"email": user.email})
        if existing_user:
            logger.info(f"User {user.email} already exists.")
            return {
                "message": "User already exists",
                "user": serialize_user(existing_user),
            }

        new_user = {
            "name": user.name or "Anonymous",
            "email": user.email or "N/A",
            "imageUrl": user.imageUrl,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
        }

        result = await users_collection.insert_one(new_user)
        new_user["_id"] = result.inserted_id

        logger.info(f"New user {user.email} stored successfully.")
        return {
            "message": "User stored successfully",
            "user": serialize_user(new_user),
        }
    except Exception as e:
        logger.error(f"Error storing user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get User API
@app.get("/auth/get-user/{user_id}")
async def get_user(user_id: str, db=Depends(get_database)):
    try:
        obj_id = ObjectId(user_id)
    except errors.InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID format"
        )

    users_collection = db["users"]
    user = await users_collection.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return serialize_user(user)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Backend running. Go to /static/index.html for the UI."}

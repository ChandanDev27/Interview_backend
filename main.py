from fastapi import FastAPI, HTTPException
from datetime import datetime
from bson import ObjectId, errors

from app.database import (
    MongoDBManager
)
from app.routers import (
    auth, user, interview, facial_analysis,
    speech_analysis, interview_question
)
from app.routers.websocket import router as websocket_router
from app.schemas.user import User

app = FastAPI()

# Initialize MongoDB Manager
mongo_manager = MongoDBManager()

# FastAPI Lifecycle Events


@app.on_event("startup")
async def startup_event():
    await mongo_manager.connect()


@app.on_event("shutdown")
async def shutdown_event():
    await mongo_manager.close()

# Include Routers
app.include_router(auth.router, prefix="/auth")
app.include_router(user.router)
app.include_router(interview.router, prefix="/api")
app.include_router(websocket_router, prefix="/api")
app.include_router(facial_analysis.router)
app.include_router(speech_analysis.router)
app.include_router(interview_question.router, prefix="/questions")

# Async MongoDB Collection
users_collection = mongo_manager.get_database()["users"]

# Convert MongoDB document to dictionary


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
async def store_user(user: User):
    try:
        existing_user = await users_collection.find_one({"email": user.email})
        if existing_user:
            return {
                "message": "User already exists",
                "user": serialize_user(existing_user),
            }

        new_user = {
            "name": user.name or "Anonymous",
            "email": user.email or "N/A",
            "imageUrl": user.imageUrl,
            "createdAt": user.createdAt,
            "updatedAt": user.updatedAt,
        }

        result = await users_collection.insert_one(new_user)
        new_user["_id"] = result.inserted_id

        return {
            "message": "User stored successfully",
            "user": serialize_user(new_user),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# Get User API


@app.get("/auth/get-user/{user_id}")
async def get_user(user_id: str):
    try:
        obj_id = ObjectId(user_id)
    except errors.InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID format"
        )

    user = await users_collection.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return serialize_user(user)

# MongoDB Health Check


@app.get("/health")
async def health_check():
    try:
        await mongo_manager.get_database().command('ping')
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"MongoDB connection error: {str(e)}"
        )


# Root endpoint
@app.get("/")
async def root():
    return {"message": "AI Interview API is running!"}

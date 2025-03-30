from fastapi import FastAPI, HTTPException, Depends
from datetime import datetime
from bson import ObjectId, errors
from app.database import MongoDBManager, get_database
from app.routers import (
    auth, user, interview, facial_analysis,
    speech_analysis, interview_question
)
from app.routers.websocket import router as websocket_router
from app.schemas.user import User
from app.config import settings, logger
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

app = FastAPI()

# Initialize MongoDB Manager
mongo_manager = MongoDBManager(
    uri=settings.MONGO_URI,
    db_name=settings.MONGO_DB_NAME,
    settings=settings
)

# FastAPI Lifecycle Events


@app.on_event("startup")
async def startup_event():
    await mongo_manager.connect()


@app.on_event("shutdown")
async def shutdown_event():
    await mongo_manager.close()

# Include Routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(user.router)
app.include_router(interview.router)
app.include_router(websocket_router, prefix="/api")
app.include_router(facial_analysis.router)
app.include_router(speech_analysis.router)
app.include_router(interview_question.router, prefix="/questions")


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"message": "Too many requests! Please try again later."}
    )


# Convert MongoDB document to dictionary
def serialize_user(user):
    return {
        "id": str(user["_id"]),
        "name": user.get("name", "Anonymous"),
        "email": user.get("email", "N/A"),
        "imageUrl": user.get("imageUrl", ""),
        "createdAt": user.get("createdAt", datetime.utcnow()),  # Use actual MongoDB value
        "updatedAt": user.get("updatedAt", datetime.utcnow()),  # Use actual MongoDB value
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


# MongoDB Health Check
@app.get("/health")
async def health_check(db=Depends(get_database)):
    try:
        await db.command("ping")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"MongoDB connection error: {str(e)}"
        )


# Root endpoint
@app.get("/")
async def root():
    return {"message": "Interview Genie API is running!"}

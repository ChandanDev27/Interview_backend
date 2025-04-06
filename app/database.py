from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from app.config import logger
import os

load_dotenv()

# Load MongoDB configurations
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
DB_NAME = os.getenv("DB_NAME", "ai_interview")

# MongoDB settings
MONGODB_SETTINGS = {
    'serverSelectionTimeoutMS': 10000,
    'connectTimeoutMS': 10000,
    'socketTimeoutMS': 15000,
}


class MongoDBManager:
    """MongoDB Connection Manager"""

    def __init__(self, uri: str, db_name: str, settings: dict):
        self.uri = uri
        self.db_name = db_name
        self.settings = settings
        self.client: AsyncIOMotorClient | None = None
        self.db = None

    async def connect(self):
        if not self.client:
            try:
                self.client = AsyncIOMotorClient(self.uri, **MONGODB_SETTINGS)
                self.db = self.client[self.db_name]
                logger.info(f"✅ Connected to MongoDB: {self.db_name}")
            except Exception as e:
                logger.error(f"❌ Error connecting to MongoDB: {e}", exc_info=True)
                raise

    async def close(self):  
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("✅ MongoDB connection closed.")

    
    async def get_collection(self, name: str):
        """Returns a MongoDB collection object after ensuring connection."""
        if not self.client:
            await self.connect()
        return self.db[name]


# Initialize MongoDB Manager
mongodb_manager = MongoDBManager(MONGO_URI, DB_NAME, MONGODB_SETTINGS)

# Define the database instance
database = mongodb_manager.db


async def get_database():
    """
    Ensures the database connection is established before using it.
    """
    if not mongodb_manager.client:
        await mongodb_manager.connect()
    return mongodb_manager.db


async def ensure_indexes():
    db = await get_database()
    await db["interviews"].create_index([("user_id", 1)])
    await db["interviews"].create_index([("created_at", 1)])
    await db["interviews"].create_index([("status", 1)])
    await db["interviews"].create_index([("session_id", 1)])
    await db["facial_analysis"].create_index([("session_id", 1)])
    await db["speech_analysis"].create_index([("session_id", 1)])


# Explicitly export variables
__all__ = ["database", "mongodb_manager", "get_database", "ensure_indexes"]

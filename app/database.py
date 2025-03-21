from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from app.config import logger
from decouple import config

# Load environment variables
load_dotenv()

MONGO_URI = config("MONGO_URI", default="mongodb://localhost:27017/")
DB_NAME = config("DB_NAME", default="ai_interview")

if not MONGO_URI or not DB_NAME:
    logger.error("Environment variables MONGO_URI and DB_NAME must be set.")
    raise ValueError("Missing required environment variables.")

MONGODB_SETTINGS = {
    'serverSelectionTimeoutMS': 30000,
    'connectTimeoutMS': 30000,
    'socketTimeoutMS': 30000,
}


class MongoDBManager:
    """MongoDB Connection Manager"""
    def __init__(self, uri: str, db_name: str, settings: dict):
        self.uri = uri
        self.db_name = db_name
        self.settings = settings
        self.client = None
        self.db = None

    async def connect(self):
        """Establish MongoDB connection"""
        try:
            self.client = AsyncIOMotorClient(self.uri, **self.settings, retryWrites=True)
            self.db = self.client[self.db_name]
            logger.info("✅ Connected to MongoDB successfully.")
        except Exception as e:
            logger.error(f"❌ Error connecting to MongoDB: {e}", exc_info=True)
            raise

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB connection closed.")

# Initialize MongoDB connection


mongodb_manager = MongoDBManager(MONGO_URI, DB_NAME, MONGODB_SETTINGS)


async def get_database():
    """Returns the MongoDB database instance"""
    if not mongodb_manager.client:
        await mongodb_manager.connect()
    return mongodb_manager.db

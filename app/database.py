from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from app.config import logger, settings

load_dotenv()

# Load MongoDB configurations
MONGO_URI = settings.MONGO_URI
DB_NAME = settings.MONGO_DB_NAME

# MongoDB Client
client = AsyncIOMotorClient(MONGO_URI)
database = client[DB_NAME]  # This is your MongoDB database instance

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


# Initialize MongoDB Manager
mongodb_manager = MongoDBManager(MONGO_URI, DB_NAME, MONGODB_SETTINGS)


async def get_database():
    """
    Ensures the database connection is established before using it.
    """
    if not mongodb_manager.client:
        await mongodb_manager.connect()
    return mongodb_manager.db

# Explicitly export variables
__all__ = ["database", "mongodb_manager", "get_database"]

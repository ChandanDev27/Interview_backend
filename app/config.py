import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    # Application configuration settings.
    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key_for_development_only")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # MongoDB Configuration
    MONGODB_SETTINGS = {
        'host': os.getenv("MONGO_HOST", "localhost"),
        'port': int(os.getenv("MONGO_PORT", 27017)),
        'serverSelectionTimeoutMS': 30000,
        'connectTimeoutMS': 30000,
        'socketTimeoutMS': 30000,
    }

    # Logging Level (DEBUG for development, INFO for production)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    @staticmethod
    def setup_logger():
        logger = logging.getLogger("AI Interview App")
        if not logger.hasHandlers():
            logger.setLevel(getattr(logging, Settings.LOG_LEVEL, logging.INFO))
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
        return logger

# Initialize settings & logger


settings = Settings()
logger = settings.setup_logger()

# Warn if SECRET_KEY is not changed
if settings.SECRET_KEY == "default_secret_key_for_development_only":
    logger.warning("⚠️ Using the default SECRET_KEY! Change it in production.")

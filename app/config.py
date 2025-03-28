import os
import logging
import urllib.parse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    if not SECRET_KEY or SECRET_KEY == "default_secret_key_for_development_only":
        raise ValueError("❌ SECRET_KEY is missing or using an insecure default!")

    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # MongoDB Configuration
    MONGO_USER = os.getenv("MONGO_USER", "")
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
    MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
    MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
    MONGO_DB_NAME = os.getenv("DB_NAME", "ai_interview")

    # Construct MongoDB URI Securely
    if MONGO_USER and MONGO_PASSWORD:
        encoded_user = urllib.parse.quote_plus(MONGO_USER)
        encoded_password = urllib.parse.quote_plus(MONGO_PASSWORD)
        MONGO_URI = f"mongodb://{encoded_user}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource=admin"
    else:
        MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}"

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def setup_logger(cls):
        # Configures and returns a logger instance.
        logger = logging.getLogger("AI Interview App")
        if not logger.hasHandlers():
            logger.setLevel(getattr(logging, cls.LOG_LEVEL, logging.INFO))
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s'))
            logger.addHandler(handler)
        return logger


# Initialize settings & logger
settings = Settings()
logger = settings.setup_logger()

import os
import logging
import urllib.parse
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class Settings:
    # Secret Key and JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    if not SECRET_KEY or SECRET_KEY == "default_secret_key_for_development_only":
        raise ValueError("❌ SECRET_KEY is missing or using an insecure default!")

    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # MongoDB Configuration
    MONGO_USER: str = os.getenv("MONGO_USER", "")
    MONGO_PASSWORD: str = os.getenv("MONGO_PASSWORD", "")
    MONGO_HOST: str = os.getenv("MONGO_HOST", "localhost")
    MONGO_PORT: int = int(os.getenv("MONGO_PORT", 27017))
    MONGO_DB_NAME: str = os.getenv("DB_NAME", "ai_interview")

    if MONGO_USER and MONGO_PASSWORD:
        encoded_user = urllib.parse.quote_plus(MONGO_USER)
        encoded_password = urllib.parse.quote_plus(MONGO_PASSWORD)
        MONGO_URI = f"mongodb://{encoded_user}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource=admin"
    else:
        MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}"

    # Email Configuration
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", SMTP_USERNAME)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))

    # App Meta
    APP_NAME: str = os.getenv("APP_NAME", "Interview Genie")
    SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@example.com")

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def setup_logger(cls) -> logging.Logger:
        logger = logging.getLogger("AI Interview App")

        # Prevent duplicate handlers
        if not logger.hasHandlers():
            logger.setLevel(getattr(logging, cls.LOG_LEVEL, logging.INFO))
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(logging.Formatter(
                "[%(asctime)s] [%(levelname)s] - %(message)s"
            ))
            logger.addHandler(stream_handler)

        return logger


# Initialize and expose config and logger
settings = Settings()
logger = settings.setup_logger()

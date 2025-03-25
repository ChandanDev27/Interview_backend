from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..services.auth import authenticate_user, create_access_token
from ..services.utils import get_password_hash
from ..database import get_database
from ..schemas.user import UserCreate, UserResponse
from app.config import settings

# Initialize Router and Rate Limiter
router = APIRouter(tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


@router.post("/token")
@limiter.limit("5/minute")  # Rate limit: 5 requests per minute
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    logger.info(f"🔍 Login attempt for: {form_data.username}")

    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"❌ Failed login attempt for {form_data.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["client_id"]}, expires_delta=access_token_expires
    )

    logger.info(f"✅ Token issued for {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    # Register a new user with hashed password and initial role.
    try:
        db = await get_database()

        logger.debug(f"🔹 Received registration request: {user.dict()}")

        existing_count = await db["users"].count_documents(
            {"client_id": user.client_id}
        )
        if existing_count > 0:
            logger.warning(
                f"⚠️ Registration failed: Client ID '{user.client_id}' already exists"
            )
            raise HTTPException(
                status_code=400, detail="Client ID already registered"
            )

        if not user.client_secret or not isinstance(user.client_secret, str):
            raise HTTPException(status_code=400, detail="Client secret must be a valid string")

        hashed_password = get_password_hash(user.client_secret)

        new_user = {
            "client_id": user.client_id,
            "client_secret": hashed_password,
            "role": user.role,
            "interviews": []
        }

        await db["users"].insert_one(new_user)
        logger.info(f"✅ New client '{user.client_id}' registered successfully")

        return {"message": "Client registered successfully"}

    except Exception as e:
        logger.exception(f"❌ Error registering user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

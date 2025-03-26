from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..services.auth import authenticate_user, create_access_token
from ..services.utils import get_password_hash
from ..database import get_database
from ..schemas.user import UserCreate, UserResponse
from app.config import settings

router = APIRouter(tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


@router.post("/token")
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["client_id"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    try:
        db = await get_database()
        existing_user = await db["users"].find_one({"client_id": user.client_id})
        if existing_user:
            raise HTTPException(status_code=400, detail="Client ID already registered")

        hashed_password = get_password_hash(user.client_secret)

        new_user = {
            "client_id": user.client_id,
            "client_secret": hashed_password,
            "role": user.role,
            "interviews": []
        }

        await db["users"].insert_one(new_user)
        return UserResponse(client_id=user.client_id, role=user.role)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

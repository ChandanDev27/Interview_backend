import random
import asyncio
import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..services.email import send_otp_email
from ..services.auth import authenticate_user, create_access_token
from ..services.utils import get_password_hash
from ..database import get_database
from ..schemas.user import UserCreate, UserResponse, TokenResponse, LoginRequest
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


class OTPRequest(BaseModel):
    email: EmailStr


otp_store = {}

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


@router.post("/token", response_model=TokenResponse)
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
        data={"sub": user["client_id"], "role": user["role"]},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    db = await get_database()

    existing_user = await db["users"].find_one({"email": user.email.lower()})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.client_secret)

    otp = str(random.randint(100000, 999999))

    new_user = {
        "client_id": user.client_id,
        "client_secret": hashed_password,
        "role": user.role,
        "email": user.email.lower(),
        "otp": otp,
        "is_verified": False
    }

    await db["users"].insert_one(new_user)
    asyncio.create_task(send_otp_email(user.email, otp))
    return UserResponse(client_id=user.client_id, role=user.role)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    user = await authenticate_user(request.email, request.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token({"sub": user["client_id"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/send-otp")
async def send_otp(request: OTPRequest):
    db = await get_database()
    email = request.email.strip().lower()

    user = await db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = str(random.randint(100000, 999999))

    await db["users"].update_one(
        {"email": email},
        {"$set": {"otp": otp, "otp_expires_at": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)}}
    )

    asyncio.create_task(send_otp_email(email, otp))
    return {"message": "OTP sent successfully"}


@router.post("/verify-otp")
async def verify_otp(request: OTPRequest):
    db = await get_database()
    email = request.email.strip().lower()

    user = await db["users"].find_one({"email": email})
    if not user or user.get("otp") is None:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if user["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if datetime.datetime.utcnow() > user.get("otp_expires_at", datetime.datetime.utcnow()):
        raise HTTPException(status_code=400, detail="OTP expired")

    await db["users"].update_one({"email": email}, {"$unset": {"otp": "", "otp_expires_at": ""}})
    return {"message": "OTP verified successfully"}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    db = await get_database()
    user = await db["users"].find_one({"email": request.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_otp = str(random.randint(100000, 999999))

    await db["users"].update_one(
        {"email": request.email},
        {"$set": {"reset_otp": reset_otp}}
    )

    asyncio.create_task(send_otp_email(request.email, reset_otp))
    return {"message": "OTP sent for password reset"}


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    db = await get_database()
    user = await db["users"].find_one({"email": request.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("reset_otp") != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    hashed_password = get_password_hash(request.new_password)

    await db["users"].update_one(
        {"email": request.email},
        {"$set": {"client_secret": hashed_password}, "$unset": {"reset_otp": ""}}
    )

    return {"message": "Password reset successful"}

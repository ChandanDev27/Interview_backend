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
from ..schemas.user import UserCreate, UserResponse
from app.config import settings

router = APIRouter(tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


class OTPRequest(BaseModel):
    email: EmailStr


otp_store = {}

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

    if "client_id" not in user:
        raise HTTPException(status_code=500, detail="User data corrupted: missing client_id")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["client_id"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    try:
        db = await get_database()
        if not user.client_id or not user.client_secret:
            raise HTTPException(status_code=400, detail="Client ID and Client Secret are required.")

        existing_user = await db["users"].find_one({"client_id": user.client_id})
        if existing_user:
            raise HTTPException(status_code=400, detail="Client ID already registered")

        hashed_password = get_password_hash(user.client_secret)

        otp = str(random.randint(100000, 999999))

        new_user = {
            "client_id": user.client_id,
            "client_secret": hashed_password,
            "role": user.role,
            "email": user.email,
            "otp": otp,
            "is_verified": False
        }

        await db["users"].insert_one(new_user)
        asyncio.create_task(send_otp_email(user.email, otp))
        return UserResponse(client_id=user.client_id, role=user.role)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str


@router.post("/auth/send-otp")
async def send_otp(request: OTPRequest):
    email = request.email
    user = await get_database["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = str(random.randint(100000, 999999))
    otp_store[email] = {"otp": otp, "expires_at": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)}

    print(f"OTP for {email}: {otp}")

    return {"message": "OTP sent successfully"}


@router.post("/auth/verify-otp")
async def verify_otp(request: OTPVerifyRequest):
    email = request.email
    otp = request.otp

    if email not in otp_store or otp_store[email]["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if datetime.datetime.utcnow() > otp_store[email]["expires_at"]:
        raise HTTPException(status_code=400, detail="OTP expired")

    del otp_store[email]

    return {"message": "OTP verified successfully"}


@router.post("/forgot-password")
async def forgot_password(email: str):
    db = await get_database()
    user = await db["users"].find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate OTP for password reset
    reset_otp = str(random.randint(100000, 999999))

    await db["users"].update_one(
        {"email": email},
        {"$set": {"reset_otp": reset_otp}}
    )

    # Send OTP to email
    asyncio.create_task(send_otp_email(email, reset_otp))

    return {"message": "OTP sent to email for password reset"}


@router.post("/reset-password")
async def reset_password(email: str, otp: str, new_password: str):
    db = await get_database()
    user = await db["users"].find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("reset_otp") != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    hashed_password = get_password_hash(new_password)

    await db["users"].update_one(
        {"email": email},
        {"$set": {"client_secret": hashed_password, "reset_otp": None}}
    )

    return {"message": "Password reset successful"}

import uuid
import secrets
import random
import asyncio
import datetime
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..services.email import send_otp_email
from ..services.auth import authenticate_user, create_access_token
from ..services.utils import get_password_hash
from ..database import get_database
from ..schemas.user import UserCreate, UserResponse, LoginRequest, VerifyOTPRequest, ForgotPasswordRequest, ResetPasswordRequest
from ..schemas.token import TokenResponse
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


class OTPRequest(BaseModel):
    email: EmailStr


otp_store = {}


@router.post("/token", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login_for_access_token(request: Request, login_data: LoginRequest):
    print(f"🔍 Attempting login for: {login_data.email}")
    user = await authenticate_user(login_data.email, login_data.password)

    if not user:
        print("❌ Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # If user is found and password matches, generate token
    access_token = create_access_token(data={"sub": user["client_id"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse)
async def register(request: Request, user: UserCreate):
    db = await get_database()

    # Check if email already exists
    existing_user = await db["users"].find_one({"email": user.email.lower()})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 🔹 Auto-generate `client_id` and `client_secret`
    client_id = str(uuid.uuid4())  # Unique identifier
    client_secret = secrets.token_hex(16)  # Secure 32-character hex string
    hashed_password = get_password_hash(client_secret)
    otp = str(random.randint(100000, 999999))

    # Create new user document
    new_user = {
        "client_id": client_id,
        "client_secret": hashed_password,
        "role": user.role,
        "email": user.email.lower(),
        "otp": otp,
        "is_verified": False
    }

    # Insert into MongoDB
    result = await db["users"].insert_one(new_user)

    # Send OTP email asynchronously
    asyncio.create_task(send_otp_email(user.email, otp))

    return UserResponse(
        id=str(result.inserted_id),  # Convert ObjectId to string
        client_id=client_id,
        email=user.email,
        role=user.role
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest):
    print(f"🔍 Login attempt for email: {body.email}")

    user = await authenticate_user(body.email, body.password)

    if not user:
        print("❌ Authentication failed: Invalid email or password")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    print(f"✅ User authenticated: {user['email']} (Role: {user['role']})")

    access_token = create_access_token({"sub": user["client_id"], "role": user["role"]})
    print(f"🔑 Access token generated for {user['email']}")
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/send-otp")
async def send_otp(request: Request, body: OTPRequest):
    db = await get_database()
    email = body.email.strip().lower()

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
async def verify_otp(request: Request, body: VerifyOTPRequest):
    db = await get_database()
    email = body.email.strip().lower()

    user = await db["users"].find_one({"email": email})
    if not user or user.get("otp") is None:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Check OTP expiration safely
    otp_expiry = user.get("otp_expires_at", datetime.datetime.utcnow())
    if datetime.datetime.utcnow() > otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired")

    if user["otp"] != body.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    await db["users"].update_one({"email": email}, {"$unset": {"otp": "", "otp_expires_at": ""}})
    return {"message": "OTP verified successfully"}


@router.post("/forgot-password")
async def forgot_password(request: Request, body: ForgotPasswordRequest):
    db = await get_database()
    user = await db["users"].find_one({"email": body.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_otp = str(random.randint(100000, 999999))

    await db["users"].update_one(
        {"email": body.email},
        {"$set": {
            "reset_otp": reset_otp,
            "reset_otp_expires_at": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        }}
    )

    asyncio.create_task(send_otp_email(body.email, reset_otp))
    return {"message": "OTP sent for password reset"}


@router.post("/reset-password")
async def reset_password(request: Request, body: ResetPasswordRequest):
    db = await get_database()
    user = await db["users"].find_one({"email": body.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check OTP expiration
    reset_otp_expiry = user.get("reset_otp_expires_at", datetime.datetime.utcnow())
    if datetime.datetime.utcnow() > reset_otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired")

    if user.get("reset_otp") != body.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    hashed_password = get_password_hash(body.new_password)

    await db["users"].update_one(
        {"email": body.email},
        {"$set": {"client_secret": hashed_password}, "$unset": {"reset_otp": "", "reset_otp_expires_at": ""}}
    )

    return {"message": "Password reset successful"}

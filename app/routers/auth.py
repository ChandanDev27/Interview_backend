import uuid
import random
import asyncio
import datetime
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..services.email import send_otp_email
from ..services.auth import authenticate_user, create_access_token
from ..services.utils import get_password_hash  # Corrected import for password hashing
from ..database import get_database
from ..schemas.auth import ForgotPasswordRequest, ResetPasswordRequest, VerifyOtpRequest
from ..schemas.user import UserCreate, UserResponse, LoginRequest
from ..schemas.token import TokenResponse
from app.config import settings

# Initialize router and rate limiter
router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)

# Token expiration time from config
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


@router.post("/register", response_model=UserResponse)
async def register(request: Request, user: UserCreate):
    db = await get_database()

    # Check if email already exists
    existing_user = await db["users"].find_one({"email": user.email.lower()})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Generate unique client ID and secure password
    client_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user.password)  # Use proper hashing function
    otp = str(random.randint(100000, 999999))

    # Create new user document
    new_user = {
        "client_id": client_id,
        "email": user.email.lower(),
        "password": hashed_password,
        "role": user.role,
        "otp": otp,
        "is_verified": False,
        "otp_expires_at": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)  # OTP expires in 5 minutes
    }

    # Insert user into MongoDB
    result = await db["users"].insert_one(new_user)

    # Send OTP asynchronously
    asyncio.create_task(send_otp_email(user.email, otp))

    return UserResponse(
        id=str(result.inserted_id),
        client_id=client_id,
        email=user.email,
        role=user.role
    )


@router.post("/verify-otp")
async def verify_otp(request: Request, body: VerifyOtpRequest):
    db = await get_database()
    email = body.email.strip().lower()

    # Check if user exists and OTP is available
    user = await db["users"].find_one({"email": email})
    if not user or user.get("otp") is None:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Check OTP expiration
    otp_expiry = user.get("otp_expires_at", datetime.datetime.utcnow())
    if datetime.datetime.utcnow() > otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired")

    if user["otp"] != body.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Mark user as verified and remove OTP from database
    await db["users"].update_one({"email": email}, {"$set": {"is_verified": True}, "$unset": {"otp": "", "otp_expires_at": ""}})
    return {"message": "OTP verified successfully"}


@router.post("/forgot-password")
@limiter.limit("3/minute")  # 3 attempts per minute to prevent abuse
async def forgot_password(request: Request, body: ForgotPasswordRequest):
    db = await get_database()

    # Check if the user exists
    user = await db["users"].find_one({"email": body.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate a 6-digit OTP and set expiration time
    reset_otp = str(random.randint(100000, 999999))
    reset_otp_expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

    # Store OTP in the database with expiry
    await db["users"].update_one(
        {"email": body.email},
        {"$set": {
            "reset_otp": reset_otp,
            "reset_otp_expires_at": reset_otp_expires_at
        }}
    )

    # Send OTP asynchronously
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

    # Hash the new password
    hashed_password = get_password_hash(body.new_password)

    # Update password and remove OTP fields
    await db["users"].update_one(
        {"email": body.email},
        {"$set": {"password": hashed_password}, "$unset": {"reset_otp": "", "reset_otp_expires_at": ""}}
    )

    return {"message": "Password reset successful"}


@router.post("/token", response_model=TokenResponse)
@limiter.limit("5/minute")  # Limit login attempts to prevent brute force attacks
async def login_for_access_token(request: Request, login_data: LoginRequest):
    print(f"🔍 Attempting login for: {login_data.email}")
    user = await authenticate_user(login_data.email, login_data.password)

    if not user:
        print("❌ Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate JWT token
    access_token = create_access_token(data={"sub": user["client_id"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

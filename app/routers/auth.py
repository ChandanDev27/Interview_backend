import uuid
import random
import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..services.email import send_otp_email
from ..services.auth import generate_otp, verify_otp_service, authenticate_user, create_access_token
from ..services.utils import get_password_hash  # Corrected import for password hashing
from ..database import get_database
from ..schemas.auth import ForgotPasswordRequest, ResetPasswordRequest, VerifyOtpRequest
from ..schemas.user import UserCreate, UserResponse, LoginRequest, OTPRequest, OTPResponse
from ..schemas.token import TokenResponse
from app.config import settings

# Initialize router and rate limiter
router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)

otp_store = {}
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
    hashed_password = get_password_hash(user.password)

    # Generate OTP
    otp_response = await generate_otp(user.email, user.Name)
    print(f"🔍 OTP Response: {otp_response}")  # Debugging line

    if "error" in otp_response:
        raise HTTPException(status_code=400, detail=otp_response["error"])

    otp = otp_response["otp"]
    print(f"Generated OTP: {otp}")

    # Create new user document (Ensure OTP is stored here)
    new_user = {
        "client_id": client_id,
        "Name": user.Name,
        "email": user.email.lower(),
        "password": hashed_password,
        "role": user.role,
        "is_verified": False,
        "otp": otp,  # Store OTP in the database
        "otp_expires_at": datetime.utcnow() + timedelta(minutes=5)
    }

    # Insert user into MongoDB
    result = await db["users"].insert_one(new_user)

    email_response = await send_otp_email(user.email, user.Name, otp)

    if email_response is False:
        raise HTTPException(status_code=500, detail="Failed to send OTP")

    return UserResponse(
        id=str(result.inserted_id),
        client_id=client_id,
        Name=user.Name,
        email=user.email,
        role=user.role
    )


@router.post("/generate-otp")
async def generate_otp_route(email: str, user_name: str):
    otp_response = await generate_otp(email, user_name)

    print(f"🔍 OTP Response: {otp_response}")  # Debugging line

    if "error" in otp_response:
        raise HTTPException(status_code=400, detail=otp_response["error"])

    return {"otp": otp_response["otp"]}


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    user = await authenticate_user(request.email, request.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token({"sub": user["client_id"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/verify-otp")
async def verify_otp(request: Request, body: VerifyOtpRequest):
    # Call the service to verify OTP
    return await verify_otp_service(body.email, body.otp)


@router.post("/forgot-password")
@limiter.limit("3/minute")  # 3 attempts per minute to prevent abuse
async def forgot_password(request: Request, body: ForgotPasswordRequest):
    db = await get_database()

    # Check if the user exists
    user = await db["users"].find_one({"email": body.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_name = user.get("Name", "User")

    # Generate a 6-digit OTP and set expiration time
    reset_otp = str(random.randint(100000, 999999))
    reset_otp_expires_at = datetime.utcnow() + timedelta(minutes=5)

    # Store OTP in the database with expiry
    await db["users"].update_one(
        {"email": body.email},
        {"$set": {
            "reset_otp": reset_otp,
            "reset_otp_expires_at": reset_otp_expires_at
        }}
    )

    # Send OTP asynchronously
    asyncio.create_task(send_otp_email(body.email, user_name, reset_otp))

    return {"message": "OTP sent for password reset"}


@router.post("/reset-password")
async def reset_password(request: Request, body: ResetPasswordRequest):
    db = await get_database()
    user = await db["users"].find_one({"email": body.email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check OTP expiration
    reset_otp_expiry = user.get("reset_otp_expires_at", datetime.utcnow())
    if datetime.utcnow() > reset_otp_expiry:
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


@router.post("/send-otp/", response_model=OTPResponse)
async def send_otp(request: OTPRequest):
    response = await send_otp_email(request.email)

    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])

    return OTPResponse(message=response["message"])

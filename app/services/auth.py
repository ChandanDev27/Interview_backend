import bcrypt
import random
import re
import logging
from datetime import datetime, timedelta
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from app.schemas.enums import UserRole
from app.config import settings
from app.database import get_database
from .email import send_otp_email, send_admin_notification_email, send_welcome_email

# Configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
MAX_OTP_ATTEMPTS = 5
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCK_DURATION = timedelta(minutes=15)
DEFAULT_EXPIRY = timedelta(hours=1)

# Logger and security tools
logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_registration_role(role: UserRole):
    if role != UserRole.candidate:
        raise HTTPException(
            status_code=403,
            detail="Only candidates can self-register. HR and Admin accounts must be created by an administrator."
        )


async def get_user(client_id: str):
    try:
        db = await get_database()
        user = await db["users"].find_one({"client_id": client_id})

        if user:
            return {
                "client_id": str(user["client_id"]),
                "Name": user["Name"],
                "email": user["email"],
                "role": user["role"]
            }

        logger.warning(f"⚠️ User not found: {client_id}")
        return None

    except Exception as e:
        logger.error(f"❌ Error fetching user from DB: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


def validate_password(password: str):
    try:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("Password must contain at least one special character")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


async def authenticate_user(email: str, password: str):
    db = await get_database()
    user = await db["users"].find_one({"email": email.lower()})

    if not user or "password" not in user:
        return None

    # Unlock account if lock period has passed
    if user.get("locked_until") and datetime.utcnow() >= user["locked_until"]:
        await db["users"].update_one(
            {"email": email.lower()},
            {
                "$set": {"login_attempts": 0},
                "$unset": {"is_locked": "", "locked_until": ""}
            }
        )
        user["login_attempts"] = 0
        user.pop("is_locked", None)
        user.pop("locked_until", None)

    # Still locked?
    if user.get("is_locked"):
        locked_until = user.get("locked_until", datetime.utcnow())
        if datetime.utcnow() < locked_until:
            remaining_time = locked_until - datetime.utcnow()
            minutes, seconds = divmod(remaining_time.total_seconds(), 60)
            raise HTTPException(
                status_code=403,
                detail=f"Account temporarily locked. Try again in {int(minutes)} minutes and {int(seconds)} seconds."
            )

    # Verify password
    if not verify_password(password, user["password"]):
        await db["users"].update_one(
            {"email": email.lower()},
            {"$inc": {"login_attempts": 1}}
        )

        user = await db["users"].find_one({"email": email.lower()})
        if user.get("login_attempts", 0) >= MAX_LOGIN_ATTEMPTS:
            await db["users"].update_one(
                {"email": email.lower()},
                {"$set": {
                    "is_locked": True,
                    "locked_until": datetime.utcnow() + ACCOUNT_LOCK_DURATION
                }}
            )
            raise HTTPException(status_code=403, detail="Account locked due to failed login attempts")

        return None

    # Reset login attempts
    await db["users"].update_one(
        {"email": email.lower()},
        {"$set": {"login_attempts": 0}, "$unset": {"is_locked": "", "locked_until": ""}}
    )

    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        client_id: str = payload.get("sub")
        if client_id is None:
            raise credentials_exception

    except ExpiredSignatureError:
        logger.error("❌ Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError:
        logger.error("❌ Invalid JWT token")
        raise credentials_exception

    user = await get_user(client_id)
    if user is None:
        raise credentials_exception

    return user


def get_current_user_role(current_user: dict = Depends(get_current_user)):
    return current_user["role"]


def require_role(required_role: str):
    def role_dependency(user_role: str = Depends(get_current_user_role)):
        if user_role not in ["admin", required_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user_role
    return role_dependency


def create_access_token(data: dict, expires_delta: timedelta = DEFAULT_EXPIRY):
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})

        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info("✅ Access token generated successfully")
        return token

    except Exception as e:
        logger.error(f"❌ Error generating access token: {str(e)}")
        raise HTTPException(status_code=500, detail="Token generation error")


async def generate_otp(email: str, user_name: str):
    try:
        otp = str(random.randint(100000, 999999))
        email_response = await send_otp_email(email, user_name, otp)
        print(f"📧 Email Response: {email_response}")

        if not email_response:
            return {"error": "Failed to send OTP"}

        return {"otp": otp}

    except Exception as e:
        print(f"⚠️ Error in generate_otp: {e}")
        return {"error": str(e)}


async def verify_otp_service(email: str, otp: str):
    db = await get_database()
    email = email.strip().lower()

    user = await db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("otp") is None:
        raise HTTPException(status_code=400, detail="OTP not found or already verified")

    if datetime.utcnow() > user.get("otp_expires_at", datetime.utcnow()):
        raise HTTPException(status_code=400, detail="OTP expired")

    if user.get("otp_attempts", 0) >= MAX_OTP_ATTEMPTS:
        raise HTTPException(status_code=403, detail="Too many failed attempts. OTP locked.")

    if user["otp"] != otp:
        await db["users"].update_one(
            {"email": email},
            {"$inc": {"otp_attempts": 1}}
        )
        raise HTTPException(status_code=400, detail="Invalid OTP")

    await db["users"].update_one(
        {"email": email},
        {
            "$set": {"is_verified": True},
            "$unset": {"otp": "", "otp_expires_at": "", "otp_sent_at": "", "otp_attempts": ""}
        }
    )

    await send_welcome_email(email, user.get("Name", "User"))

    return {"message": "OTP verified successfully"}


def generate_hr_invite_token(email: str, expires_in_minutes: int = 60):
    payload = {
        "email": email,
        "role": "hr",
        "exp": datetime.utcnow() + timedelta(minutes=expires_in_minutes),
        "type": "invite"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

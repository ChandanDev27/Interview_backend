import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt, ExpiredSignatureError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import logging
import random
import re
from app.config import settings
from app.database import get_database
from .email import send_otp_email

# Load settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
otp_db = {}

# Initialize logger
logger = logging.getLogger(__name__)

# OAuth2 token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Default token expiry time
DEFAULT_EXPIRY = timedelta(hours=1)


async def get_user(client_id: str):
    # Fetch user details from the database using client_id.
    # Returns a dictionary with user details if found, else None.
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
    # Validates password complexity:
    # - At least 8 characters long
    # - At least 1 uppercase letter
    # - At least 1 digit
    # - At least 1 special character

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
    """Hashes the password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies the password against the hashed password."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


async def authenticate_user(email: str, password: str):
    # Authenticates the user by checking email and password.
    # Returns the user document if authenticated, else None.

    try:
        db = await get_database()
        user = await db["users"].find_one({"email": email.lower()})

        if not user:
            logger.warning(f"⚠️ User not found: {email}")
            return None

        if "password" not in user:
            logger.warning("❌ Password field missing!")
            return None

        logger.info("✅ User authenticated successfully")
        return user

    except Exception as e:
        logger.error(f"❌ Error in authentication: {str(e)}")
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Decodes JWT token and fetches the current user.
    # Raises an error if the token is invalid or expired.
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
    # Extracts the user role from the current authenticated user.
    return current_user["role"]


def require_role(required_role: str):

    # Middleware to check if a user has the required role.
    # Admins are allowed to access all protected routes.
    def role_dependency(user_role: str = Depends(get_current_user_role)):
        if user_role not in ["admin", required_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user_role
    return role_dependency


def create_access_token(data: dict, expires_delta: timedelta = DEFAULT_EXPIRY):
    # Generate a JWT access token with an expiration time.
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

        # 🔍 Wait for a proper response from `send_otp_email()`
        email_response = await send_otp_email(email, user_name, otp)
        print(f"📧 Email Response: {email_response}")

        if not email_response:  # If `send_otp_email()` returns `False`
            return {"error": "Failed to send OTP"}

        return {"otp": otp}

    except Exception as e:
        print(f"⚠️ Error in generate_otp: {e}")  # Debugging
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

    # OTP valid
    await db["users"].update_one(
        {"email": email},
        {
            "$set": {"is_verified": True},
            "$unset": {"otp": "", "otp_expires_at": "", "otp_sent_at": "", "otp_attempts": ""}
        }
    )

    return {"message": "OTP verified successfully"}

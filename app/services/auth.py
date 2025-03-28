from datetime import datetime, timedelta
from jose import JWTError, jwt, ExpiredSignatureError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import logging
import re
from passlib.context import CryptContext
from app.config import settings
from app.database import get_database

# Load settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

# Initialize logger
logger = logging.getLogger(__name__)

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Default token expiry time
DEFAULT_EXPIRY = timedelta(hours=1)


async def get_user(client_id: str):
    """
    Fetch user details from the database using client_id.
    """
    try:
        db = await get_database()
        user = await db["users"].find_one({"client_id": client_id})

        if user:
            return {
                "client_id": str(user["client_id"]),
                "client_secret": user["client_secret"],
                "role": user["role"]
            }

        logger.warning(f"User  not found: {client_id}")
        return None

    except Exception as e:
        logger.error(f"Error fetching user from DB: {str(e)}")
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


async def authenticate_user(email: str, password: str):
    db = await get_database()  # Connect to the database
    user = await db["users"].find_one({"email": email.lower()})  # Find user by email

    if not user:
        print(f"❌ User not found for email: {email}")
        return None  # User not found

    print(f"🔍 Found user: {user['email']} - Checking password...")
    if not verify_password(password, user["client_secret"]):  # Check password
        print("❌ Password does not match!")
        return None  # Password mismatch

    print("✅ User authenticated successfully")
    return user  # User authenticated successfully


async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Extract and validate the user from the JWT token.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        logger.debug(f"Decoding token: {token}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        client_id: str = payload.get("sub")

        if client_id is None:
            logger.error("Client ID missing in token")
            raise credentials_exception

    except ExpiredSignatureError:
        logger.error("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError:
        logger.error("Invalid JWT token")
        raise credentials_exception

    logger.info(f"Token decoded successfully for client_id: {client_id}")

    user = await get_user(client_id)
    if user is None:
        logger.warning(f"User  not found for token client_id: {client_id}")
        raise credentials_exception

    return user


def get_current_user_role(current_user: dict = Depends(get_current_user)):
    """
    Extract the user role from the current authenticated user.
    """
    return current_user["role"]


def require_role(required_role: str):
    """
    Middleware to check if a user has the required role.
    Admins are allowed to access all protected routes.
    """
    def role_dependency(user_role: str = Depends(get_current_user_role)):
        if user_role not in ["admin", required_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user_role
    return role_dependency


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = DEFAULT_EXPIRY):
    """
    Generate a JWT access token with an expiration time.
    """
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})

        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info("Access token generated successfully")

        return token

    except Exception as e:
        logger.error(f"Error generating access token: {str(e)}")
        raise HTTPException(status_code=500, detail="Token generation error")

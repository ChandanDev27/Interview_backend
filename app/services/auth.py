from datetime import datetime, timedelta
from jose import JWTError, jwt, ExpiredSignatureError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import logging
from passlib.context import CryptContext
from ..config import SECRET_KEY, ALGORITHM
from ..database import db

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
    user = await db["users"].find_one({"client_id": str(client_id)})
    if user:
        return {
            "client_id": str(user["client_id"]),
            "client_secret": user["client_secret"],
            "role": user["role"]
        }
    logger.error(f"User not found for client_id: {client_id}")
    return None


def verify_password(plain_password, hashed_password):
    """
    Verify a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(client_id: str, password: str):
    """
    Authenticate a user by verifying their client_id and password.
    """
    logger.debug(f"Authenticating user with client_id: {client_id}")
    user = await db["users"].find_one({"client_id": client_id})
    if not user:
        logger.error("User not found in database")
        return None

    if not verify_password(password, user["client_secret"]):
        logger.error("Password verification failed")
        return None

    logger.info(f"User {client_id} authenticated successfully!")
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Extract and validate the user from the JWT token.
    """
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
        logger.error(f"User not found: {client_id}")
        raise credentials_exception

    logger.info(f"User authenticated: {user}")
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


def create_access_token(data: dict, expires_delta: timedelta = DEFAULT_EXPIRY):
    """
    Generate a JWT access token with an expiration time.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

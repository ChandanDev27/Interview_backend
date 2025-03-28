from passlib.context import CryptContext
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class WeakPasswordError(Exception):
    # Custom exception for weak passwords.
    pass


def is_password_strong(password: str) -> bool:
    # Check if password meets security requirements.
    return (
        len(password) >= 8 and
        bool(re.search(r"\d", password)) and           # At least one digit
        bool(re.search(r"[a-z]", password)) and        # At least one lowercase letter
        bool(re.search(r"[A-Z]", password)) and        # At least one uppercase letter
        bool(re.search(r"[@$!%*?&]", password))        # At least one special character
    )


def verify_password(plain_password, hashed_password):
    print(f"🔍 Comparing: {plain_password} with {hashed_password}")
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)

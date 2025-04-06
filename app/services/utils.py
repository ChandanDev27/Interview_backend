from passlib.context import CryptContext
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class WeakPasswordError(Exception):
    pass


def is_password_strong(password: str) -> bool:
    return (
        len(password) >= 8 and
        bool(re.search(r"\d", password)) and
        bool(re.search(r"[a-z]", password)) and
        bool(re.search(r"[A-Z]", password)) and
        bool(re.search(r"[@$!%*?&]", password))
    )


def hash_password(password: str) -> str:
    # Hash a password after checking strength.
    if not is_password_strong(password):
        raise WeakPasswordError("Password is too weak. It must be at least 8 characters long and include digits, uppercase, lowercase, and special characters.")
    return pwd_context.hash(password)



def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)

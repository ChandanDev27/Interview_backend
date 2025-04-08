from enum import Enum

class UserRole(str, Enum):
    candidate = "candidate"
    hr = "hr"
    admin = "admin"

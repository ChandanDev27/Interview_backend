from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import UserResponse
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    # Get the currently authenticated user's details.
    return current_user


@router.get("/admin", response_model=UserResponse)
async def get_admin(current_user: User = Depends(get_current_user)):
    # Get the admin user's details. Only accessible if the user is an admin.
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admins only."
        )
    return current_user

from fastapi import APIRouter, Depends, HTTPException, status, Body, File, UploadFile
from typing import List
from app.schemas.user import UserResponse, UserUpdate, AdminUserUpdate, ChangePasswordRequest
from app.services.auth import get_current_user, hash_password, verify_password
from app.models.user import User
from app.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import os
import shutil

AVATAR_UPLOAD_DIR = "media/avatars"
os.makedirs(AVATAR_UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    user_update: UserUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    await db["users"].update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": update_data}
    )

    updated_user = await db["users"].find_one({"_id": ObjectId(current_user.id)})
    return UserResponse(**updated_user, id=str(updated_user["_id"]))


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    filename = f"{current_user.id}_{file.filename}"
    file_path = os.path.join(AVATAR_UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    avatar_url = f"/media/avatars/{filename}"
    await db["users"].update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"avatar_url": avatar_url}}
    )

    return {"avatar_url": avatar_url}


@router.post("/me/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    new_hashed = hash_password(data.new_password)
    await db["users"].update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"hashed_password": new_hashed}}
    )

    return {"message": "Password updated successfully"}


@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admins only."
        )

    users = await db["users"].find().to_list(length=100)
    return [UserResponse(**u, id=str(u["_id"])) for u in users]


@router.patch("/{user_id}/admin-update", response_model=UserResponse)
async def admin_update_user(
    user_id: str,
    update_data: AdminUserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update other users.")

    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {k: v for k, v in update_data.model_dump().items() if v is not None}}
    )

    updated = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**updated, id=str(updated["_id"]))


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users.")

    result = await db["users"].delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}

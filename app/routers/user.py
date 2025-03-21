from fastapi import APIRouter, Depends, HTTPException, Request
from ..services.auth import get_current_user
from ..database import db
import logging

router = APIRouter(tags=["Users"])
logger = logging.getLogger(__name__)


@router.get("/user/me")
async def read_users_me(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    client_ip = request.client.host
    logger.info(
        f"User {current_user['client_id']} retrieved their profile "
        f"from {client_ip}."
    )
    return {
        "client_id": current_user["client_id"],
        "role": current_user.get("role", "user")
    }


@router.get("/admin/users")
async def get_admin_users(
    request: Request,
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
    skip: int = 0
):
    # Retrieve all users (Admin only) with pagination.
    client_ip = request.client.host

    # Secure role check
    if "role" not in current_user or current_user["role"] != "admin":
        logger.warning(
            f"❌ Unauthorized access to '/admin/users' from {client_ip} "
            f"by {current_user.get('client_id', 'Unknown')}"
        )
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        # Explicitly select only required fields
        users = await db["users"].find(
            {}, {
                "_id": 0,
                "client_id": 1,
                "username": 1,
                "email": 1,
                "role": 1
            }
        ).skip(skip).limit(limit).to_list(length=limit)

        logger.info(
            f"✅ Admin {current_user.get('client_id')} retrieved "
            f"{len(users)} users from {client_ip}."
        )
        return {"users": users, "total_retrieved": len(users)}

    except Exception as e:
        logger.error(
            f"❌ Error retrieving users by {current_user.get('client_id')}: {e}"
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")

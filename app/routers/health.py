# app/router/health.py

from fastapi import APIRouter, Depends, HTTPException
from app.database import get_database
from app.config import logger

router = APIRouter()

@router.get("/health")
async def health_check(db=Depends(get_database)):
    try:
        await db.command("ping")
        logger.info("✅ /health check succeeded")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"❌ /health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"MongoDB connection error: {str(e)}"
        )

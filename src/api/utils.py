from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.database.db import get_db_session

router = APIRouter(prefix="/api/utils", tags=["utils"])

@router.get("/healthcheck")
async def healthcheck(db: AsyncSession = Depends(get_db_session)):
    """
    Health check endpoint to verify database connectivity.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"message": "database connection successful"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database connection failed")
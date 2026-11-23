from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.response import ApiResponse
from app.core.clock import get_app_now_utc
from app.core.config import settings
from app.db.session import get_db

router = APIRouter()

@router.get("/health", response_model=ApiResponse[dict])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint providing backend status, database status, and clock info."""
    db_status = "healthy"
    try:
        # Check actual database connectivity
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"

    is_overall_healthy = db_status == "healthy"
    status_code = 200 if is_overall_healthy else 503

    return ApiResponse(
        code=status_code,
        message="Service is running healthy" if is_overall_healthy else "Database connection failed",
        data={
            "status": "healthy",
            "backend": "healthy",
            "database": db_status,
            "project": settings.PROJECT_NAME,
            "app_now": get_app_now_utc().isoformat(),
            "timezone": settings.COMPANY_TIMEZONE,
        }
    )

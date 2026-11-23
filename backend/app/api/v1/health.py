from fastapi import APIRouter
from app.core.response import ApiResponse
from app.core.clock import get_app_now_utc
from app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=ApiResponse[dict])
def health_check():
    """Health check endpoint providing service status and simulated clock value."""
    return ApiResponse.success(
        data={
            "status": "healthy",
            "project": settings.PROJECT_NAME,
            "app_now": get_app_now_utc().isoformat(),
            "timezone": settings.COMPANY_TIMEZONE,
        },
        message="Service is running healthy"
    )

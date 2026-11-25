from fastapi import APIRouter
from app.api.v1 import health, mock, auth

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(mock.router, tags=["Mock"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth & Permissions"])

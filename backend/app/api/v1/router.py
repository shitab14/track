from fastapi import APIRouter
from app.api.v1 import health, mock

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(mock.router, tags=["Mock"])

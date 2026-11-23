import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.response import ApiResponse
from app.api.v1.router import api_router

logger = logging.getLogger("track.backend")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS setup
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers ensuring { code, message, data: null } envelope
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiResponse.error(
                message=str(exc.detail),
                code=exc.status_code
            ).model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        message = "; ".join([f"{err.get('loc', ['field'])[-1]}: {err.get('msg')}" for err in errors])
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ApiResponse.error(
                message=f"Validation error: {message}",
                code=status.HTTP_422_UNPROCESSABLE_ENTITY
            ).model_dump()
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled server error: %s", str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ApiResponse.error(
                message="Internal server error",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ).model_dump()
        )

    # Route inclusion
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Root redirect / fallback health
    @app.get("/", tags=["Root"])
    def root():
        return ApiResponse.success(
            data={"api_docs": "/docs", "version": "1.0.0"},
            message="Welcome to Track Backend API"
        )

    return app

app = create_app()

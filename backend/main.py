"""
Medical Chatbot Backend API

FastAPI application providing REST endpoints for the medical chatbot system.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from .config import Settings, get_settings
from .routers import chat, upload, health, auth, admin
from .middleware import (
    LoggingMiddleware,
    ErrorHandlerMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware
)
from .database import init_db, close_db

from .scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Medical Chatbot Backend API...")
    
    settings = get_settings()
    
    # Initialize database
    await init_db(settings)
    logger.info("Database initialized")
    
    # Start background scheduler
    await start_scheduler()
    logger.info("Background scheduler started")
    
    # Initialize orchestrator (lazy loading on first request)
    logger.info("Backend ready to accept requests")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Medical Chatbot Backend API...")
    
    # Stop scheduler
    await stop_scheduler()
    logger.info("Background scheduler stopped")
    
    # Close database
    await close_db()
    logger.info("Shutdown complete")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title="Medical Chatbot API",
        description="Backend API for AI-powered medical consultation system",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan
    )
    
    # CORS — include admin panel origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Rate limiting (if enabled in settings)
    if settings.RATE_LIMIT_PER_MINUTE > 0:
        app.add_middleware(
            RateLimitMiddleware,
            per_minute=settings.RATE_LIMIT_PER_MINUTE,
            per_hour=settings.RATE_LIMIT_PER_HOUR
        )
    
    # Include routers
    app.include_router(health.router, prefix="/api", tags=["Health"])
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
    app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
    app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "service": "Medical Chatbot API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/api/docs"
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal error occurred. Please try again later.",
                "error_type": type(exc).__name__
            }
        )
    
    logger.info("FastAPI application created successfully")
    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
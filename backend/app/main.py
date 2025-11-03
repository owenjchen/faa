"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog

from app.config import settings
from app.api.v1 import conversations, resolutions, evaluations, websocket
from app.utils.logging import setup_logging
from app.utils.metrics import setup_metrics

# Setup logging
setup_logging()
logger = structlog.get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Fidelity Agent Assistant API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize services
    setup_metrics()

    # Compile LangGraph workflow on startup
    from app.agents.workflow import get_workflow
    get_workflow()

    yield

    # Shutdown
    logger.info("Shutting down Fidelity Agent Assistant API")


# Create FastAPI app with enhanced Swagger UI configuration
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Fidelity Agent Assistant API

AI-powered chatbot that empowers Fidelity service representatives to better assist customers
during live calls and chats.

### Key Features
- **Real-time conversation processing** via WebSocket
- **Agent-based workflow** with LangGraph orchestration
- **Multi-source search** (fidelity.com + myGPS)
- **AI-generated resolutions** with citations
- **Quality evaluation** with automated scoring

### Workflow
1. Customer-rep conversation triggers the agent
2. Query optimization using LLM
3. Parallel search across multiple sources
4. Resolution generation with inline citations
5. Quality evaluation and scoring
6. Representative review and approval

### Authentication
API endpoints require JWT authentication (except health check and root).
    """,
    lifespan=lifespan,
    # Swagger UI configuration
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    # OpenAPI metadata
    contact={
        "name": "FAA Support Team",
        "email": "faa-support@fidelity.com",
    },
    license_info={
        "name": "Internal Use Only",
    },
    # Swagger UI customization
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 1,
        "docExpansion": "list",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "syntaxHighlight.theme": "monokai",
        "tryItOutEnabled": True,
    },
    # OpenAPI tags metadata
    openapi_tags=[
        {
            "name": "conversations",
            "description": "Manage customer-rep conversations and messages",
        },
        {
            "name": "resolutions",
            "description": "AI-generated resolutions with citations",
        },
        {
            "name": "evaluations",
            "description": "Quality metrics and evaluation scores",
        },
        {
            "name": "websocket",
            "description": "Real-time WebSocket connections for live updates",
        },
        {
            "name": "health",
            "description": "Health check and system status",
        },
    ],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


# Health check endpoint
@app.get(
    "/health",
    tags=["health"],
    summary="Health Check",
    description="Check if the API is running and healthy",
    response_description="Health status information",
)
async def health_check():
    """
    Health check endpoint.

    Returns the current status of the API including:
    - Status (healthy/unhealthy)
    - Application version
    - Environment (development/production)
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get(
    "/",
    tags=["health"],
    summary="API Root",
    description="Get basic API information and links to documentation",
    response_description="API information",
)
async def root():
    """
    Root endpoint - API information.

    Returns basic information about the API including:
    - API name and version
    - Links to documentation
    - Available endpoints
    """
    return {
        "message": "Fidelity Agent Assistant API",
        "version": settings.APP_VERSION,
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc",
            "openapi": f"{settings.API_V1_PREFIX}/openapi.json",
        },
        "endpoints": {
            "conversations": f"{settings.API_V1_PREFIX}/conversations",
            "resolutions": f"{settings.API_V1_PREFIX}/resolutions",
            "evaluations": f"{settings.API_V1_PREFIX}/evaluations",
            "websocket": f"{settings.API_V1_PREFIX}/ws",
        },
        "health": "/health",
    }


# Include routers
app.include_router(
    conversations.router,
    prefix=f"{settings.API_V1_PREFIX}/conversations",
    tags=["conversations"],
)

app.include_router(
    resolutions.router,
    prefix=f"{settings.API_V1_PREFIX}/resolutions",
    tags=["resolutions"],
)

app.include_router(
    evaluations.router,
    prefix=f"{settings.API_V1_PREFIX}/evaluations",
    tags=["evaluations"],
)

app.include_router(
    websocket.router,
    prefix=f"{settings.API_V1_PREFIX}/ws",
    tags=["websocket"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

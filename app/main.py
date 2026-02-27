import logging
import os
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.dependencies import global_redis_client as redis_client
from app.integration.dashboard_router import router as dashboard_router
from app.integration.router import router as integration_router
from app.utils import start_scheduler

# Configure Logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


# --- Application Initialization ---


# This dictionary defines the sections (tags) visible in the Swagger UI
tags_metadata = [
    {
        "name": "Integration (Headless)",
        "description": "Endpoints for system-to-system integration (ERP, CRM) using JSON and API Keys.",
    },
    {
        "name": "Web Dashboard API",
        "description": "Endpoints used by the Frontend UI (index.html) for interactive upload and validation.",
    },
    {
        "name": "Static Pages",
        "description": "Routes that serve the static HTML content (UI).",
    },
    {
        "name": "System",
        "description": "Health checks and system status.",
    },
]

# Initialize FastAPI with metadata
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Batch Processing Engine.",
    openapi_tags=tags_metadata,
)

# Configure Jinja2 Templates
templates = Jinja2Templates(directory="templates")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup Event Handler
@app.on_event("startup")
async def startup_event():
    """Application startup tasks.

    Creates necessary directories and initializes background services.
    This ensures proper separation of concerns by moving infrastructure
    setup out of the configuration module.
    """
    settings.create_dirs()
    logger.info("Application startup complete")


# Start Cleanup Scheduler
start_scheduler(settings.TEMP_DIR, settings.CLEANUP_INTERVAL_SECONDS)


# --- Register Routers ---


app.include_router(
    integration_router,
    prefix=f"{settings.API_PREFIX}/integration",
    tags=["Integration (Headless)"],
)

app.include_router(
    dashboard_router,
    tags=["Web Dashboard API"],
)


# --- System Status (Health Checks) ---


@app.get(
    "/health",
    tags=["System"],
    summary="System Health Check",
    description="Returns the operational status of the service and its dependencies (Redis).",
    responses={
        200: {
            "description": "Service is healthy.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2026-01-01T12:00:00",
                        "version": "1.4.1",
                        "engine": "LogicPaper v1.4.1",
                        "redis": "connected",
                    }
                }
            },
        },
        503: {"description": "Service is unhealthy (e.g. Redis disconnected)."},
    },
)
async def health_check():
    """Standard Health Check.

    Returns:
        dict: Status information including timestamp and version.
    """
    try:
        redis_client.ping()
        redis_status = "connected"
        http_status = 200
        service_status = "healthy"
    except Exception:
        redis_status = "error"
        http_status = 503
        service_status = "unhealthy"

    return JSONResponse(
        status_code=http_status,
        content={
            "status": service_status,
            "timestamp": datetime.now().isoformat(),
            "version": settings.VERSION,
            "engine": f"{settings.PROJECT_NAME} v{settings.VERSION}",
            "redis": redis_status,
        },
    )


# --- Static Pages ---


@app.get(
    "/",
    tags=["Static Pages"],
    summary="Dashboard Home",
    description="Serves the main HTML dashboard interface for document generation, uploads, and monitoring.",
    response_class=HTMLResponse,
    responses={200: {"description": "HTML Dashboard loaded successfully."}},
)
async def read_root(request: Request):
    """Serves the main application page.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        TemplateResponse: The rendered index.html template.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get(
    "/help",
    tags=["Static Pages"],
    summary="Documentation Page",
    description="Serves the user guide, syntax reference, and help documentation.",
    response_class=HTMLResponse,
    responses={200: {"description": "HTML Documentation loaded successfully."}},
)
async def read_help(request: Request):
    """Serves the documentation page.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        TemplateResponse: The rendered help.html template.
    """
    return templates.TemplateResponse("help.html", {"request": request})


@app.get(
    "/history",
    tags=["Static Pages"],
    summary="Job History Page",
    description="Serves the history view of recent processing jobs and their outcomes.",
    response_class=HTMLResponse,
    responses={200: {"description": "HTML History page loaded successfully."}},
)
async def read_history(request: Request):
    """Serves the execution history page.

    Args:
        request (Request): The FastAPI request object.

    Returns:
        TemplateResponse: The rendered history.html template.
    """
    return templates.TemplateResponse("history.html", {"request": request})


# --- Static Files ---


app.mount(
    "/css", StaticFiles(directory=os.path.join(settings.STATIC_DIR, "css")), name="css"
)
app.mount(
    "/js", StaticFiles(directory=os.path.join(settings.STATIC_DIR, "js")), name="js"
)

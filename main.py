"""Parvarish AI FastAPI application entry point.

Initializes the FastAPI app and includes API routers.
"""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.routes import auth_router, chatbot_router, games_router, lacking_router
from app.routes.parent_realtime_ws import router as parent_realtime_ws_router
from app.routes.google_auth import router as google_auth_router
from app.routes.settings import router as settings_router
from app.routes.parent_routes import router as parent_router
from app.routes.parent_notifications import router as parent_notifications_router
from app.routes.behavior_routes import router as behavior_router
from app.routes.tasks import router as tasks_router
from app.routes.child_progress import router as child_progress_router
from app.routes.activity_history import router as activity_history_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.parent_realtime import set_parent_realtime_loop

    set_parent_realtime_loop(asyncio.get_running_loop())
    yield
    set_parent_realtime_loop(None)


app = FastAPI(title="Parvarish AI", version="0.1.0", lifespan=lifespan)

# Configure CORS FIRST (before session middleware) to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware (required for OAuth) - must be after CORS
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY or "your-secret-key-for-sessions",
    same_site="lax",
    https_only=False,
    max_age=86400,
)


@app.get("/health", tags=["health"])
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "Parvarish AI", "google_oauth_enabled": True}


# Include versioned API routers BEFORE mounting static files
app.include_router(auth_router, prefix="/api/v1")
app.include_router(google_auth_router, prefix="/api/v1")  # Google OAuth routes
app.include_router(settings_router, prefix="/api/v1")  # Settings & profile management
app.include_router(parent_router, prefix="/api/v1")  # Parent-specific aliases
app.include_router(parent_notifications_router, prefix="/api/v1")  # Unified notification feed
app.include_router(behavior_router, prefix="/api/v1")  # Child behavior tracking
app.include_router(tasks_router, prefix="/api/v1")  # Task generation from chatbot & behavior
app.include_router(child_progress_router, prefix="/api/v1")  # Child progress dashboard
app.include_router(activity_history_router, prefix="/api/v1")  # Child activity history (30-day tracking)
app.include_router(chatbot_router, prefix="/api/v1")  # Chatbot with child awareness
app.include_router(games_router, prefix="/api/v1")  # Games submission & analysis
app.include_router(lacking_router, prefix="/api/v1")  # Lacking analysis & task generation
app.include_router(parent_realtime_ws_router, prefix="/api/v1")  # Parent WebSocket notifications

# Serve static frontend files (must be last to not override API routes)
try:
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
except RuntimeError:
    pass  # Frontend directory doesn't exist yet

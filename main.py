"""Parvarish AI FastAPI application entry point.

Initializes the FastAPI app and includes API routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os

from app.routes import auth_router, chatbot_router
from app.routes.google_auth import router as google_auth_router
from app.routes.settings import router as settings_router
from app.routes.parent_routes import router as parent_router
from app.routes.behavior_routes import router as behavior_router
from app.routes.tasks import router as tasks_router
from app.core.config import settings

app = FastAPI(title="Parvarish AI", version="0.1.0")

# Add session middleware (required for OAuth)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY or "your-secret-key-for-sessions"
)

# Configure CORS to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(behavior_router, prefix="/api/v1")  # Child behavior tracking
app.include_router(tasks_router, prefix="/api/v1")  # Task generation from chatbot & behavior
app.include_router(chatbot_router, prefix="/api/v1")  # Chatbot with child awareness

# Serve static frontend files (must be last to not override API routes)
try:
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
except RuntimeError:
    pass  # Frontend directory doesn't exist yet

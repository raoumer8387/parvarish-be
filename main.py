"""Parvarish AI FastAPI application entry point.

Initializes the FastAPI app and includes API routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import auth_router, chatbot_router


app = FastAPI(title="Parvarish AI", version="0.1.0")

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
    return {"status": "ok", "service": "Parvarish AI"}


# Include versioned API routers BEFORE mounting static files
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chatbot_router)

# Serve static frontend files (must be last to not override API routes)
try:
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
except RuntimeError:
    pass  # Frontend directory doesn't exist yet

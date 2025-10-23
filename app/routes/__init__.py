"""API routes package.

Includes routers for authentication and chatbot endpoints.
"""

from .auth import router as auth_router
from .chatbot import router as chatbot_router

__all__ = ["auth_router", "chatbot_router"]

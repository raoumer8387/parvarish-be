"""Authentication routes (placeholders).

Provide endpoints for user registration, login, token refresh, etc.
"""

from fastapi import APIRouter, Depends

# from app.schemas import UserCreate, Token
# from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register_user():  # db: Session = Depends(get_db)
    """Register a new user (placeholder)."""
    return {"detail": "Register endpoint (placeholder)"}

@router.post("/login")
def login_user():  # db: Session = Depends(get_db)
    """Login user and return token (placeholder)."""
    return {"access_token": "placeholder", "token_type": "bearer"}

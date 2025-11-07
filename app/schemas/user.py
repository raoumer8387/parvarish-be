"""User schemas for request/response validation."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=6)
    name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str


class UserRead(UserBase):
    """Schema for user response."""
    id: int
    name: Optional[str] = None
    picture: Optional[str] = None
    google_id: Optional[str] = None
    role: str = "parent"  # All Google OAuth users are parents

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for JWT token data."""
    email: Optional[str] = None
    user_id: Optional[int] = None

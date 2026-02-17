"""
User Schemas

Pydantic models for user request/response validation
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str


class UserResponse(UserBase):
    """Schema for returning user data"""
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user data"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

"""
Auth Schemas

Pydantic models for authentication request/response validation
"""

from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data encoded in JWT token"""
    user_id: Optional[int] = None
    email: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema"""
    email: str
    password: str

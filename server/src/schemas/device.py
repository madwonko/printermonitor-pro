"""
Device Schemas

Pydantic models for proxy device request/response validation
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DeviceCreate(BaseModel):
    """Schema for registering a device"""
    name: str
    hardware_id: Optional[str] = None
    version: Optional[str] = None


class DeviceResponse(BaseModel):
    """Schema for returning device data"""
    id: int
    name: str
    status: str
    version: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceRegistrationResponse(DeviceResponse):
    """Schema for device registration response (includes API key)"""
    api_key: str

    class Config:
        from_attributes = True

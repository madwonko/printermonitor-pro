"""
Printer Schemas

Pydantic models for printer request/response validation
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PrinterCreate(BaseModel):
    """Schema for registering a printer"""
    ip: str
    name: str
    location: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None


class PrinterUpdate(BaseModel):
    """Schema for updating a printer"""
    name: Optional[str] = None
    location: Optional[str] = None
    model: Optional[str] = None


class PrinterResponse(BaseModel):
    """Schema for returning printer data"""
    id: int
    ip: str
    name: str
    location: Optional[str] = None
    model: Optional[str] = None
    connection_status: str
    last_seen_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

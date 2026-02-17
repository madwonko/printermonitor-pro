"""
Metrics Schemas

Pydantic models for printer metrics request/response validation
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class MetricsData(BaseModel):
    """Individual metrics data"""
    total_pages: Optional[int] = None
    toner_level_pct: Optional[int] = None
    toner_status: Optional[str] = None
    drum_level_pct: Optional[int] = None
    device_status: Optional[int] = None
    model: Optional[str] = None


class MetricsIngest(BaseModel):
    """Schema for ingesting metrics from proxy device"""
    printer_id: str  # IP address of printer
    timestamp: Optional[datetime] = None
    metrics: MetricsData


class MetricsResponse(BaseModel):
    """Schema for returning metrics data"""
    id: int
    printer_id: int
    timestamp: datetime
    total_pages: Optional[int] = None
    toner_level_pct: Optional[int] = None
    toner_status: Optional[str] = None
    drum_level_pct: Optional[int] = None
    device_status: Optional[int] = None

    class Config:
        from_attributes = True


class MetricsSummary(BaseModel):
    """Summary of printer metrics"""
    printer_id: int
    printer_name: str
    printer_ip: str
    location: Optional[str] = None
    latest_timestamp: Optional[datetime] = None
    total_pages: Optional[int] = None
    toner_level_pct: Optional[int] = None
    toner_status: Optional[str] = None
    drum_level_pct: Optional[int] = None
    connection_status: str

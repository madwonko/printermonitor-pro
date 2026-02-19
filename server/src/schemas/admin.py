"""
Admin Schemas

Pydantic models for admin endpoints
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class UserAdminView(BaseModel):
    """Admin view of user"""
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    
    # License info
    license_tier: str
    license_status: str
    trial_ends_at: Optional[datetime]
    device_count: int
    printer_count: int

    class Config:
        from_attributes = True


class SystemStats(BaseModel):
    """System-wide statistics"""
    total_users: int
    active_users: int
    trial_users: int
    paying_users: int
    
    total_devices: int
    active_devices: int
    
    total_printers: int
    
    revenue_monthly: int  # In cents
    revenue_yearly: int   # In cents
    
    recent_signups_7d: int
    trials_expiring_7d: int


class LicenseUpdate(BaseModel):
    """Update user's license"""
    tier_id: str  # 'free', 'maker', 'pro', 'enterprise'
    status: Optional[str] = None  # 'active', 'trial', 'cancelled'

"""
License Models

License tiers and user licenses
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from ..database import Base


class LicenseTier(Base):
    __tablename__ = "license_tiers"
    
    id = Column(String, primary_key=True)  # 'free', 'maker', 'pro', 'enterprise'
    name = Column(String, nullable=False)
    
    # Pricing (in cents)
    price_monthly = Column(Integer, nullable=False)  # 0 for free, 1000 for $10, etc.
    price_yearly = Column(Integer, nullable=False)   # Yearly discount
    
    # Limits
    max_devices = Column(Integer, nullable=False)
    max_printers = Column(Integer, nullable=False)  # -1 for unlimited
    history_days = Column(Integer, nullable=False)  # -1 for unlimited
    
    # Features (JSON)
    features = Column(JSON)  # ["basic_alerts", "api_access", etc.]
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    licenses = relationship("License", back_populates="tier")
    
    def __repr__(self):
        return f"<LicenseTier {self.id} - {self.name}>"


class License(Base):
    __tablename__ = "licenses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    tier_id = Column(String, ForeignKey("license_tiers.id"), nullable=False)
    
    # Status
    status = Column(String, default="active")  # active, trial, expired, cancelled
    
    # Dates
    starts_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # NULL for non-expiring
    trial_ends_at = Column(DateTime, nullable=True)  # 14-day trial
    
    # Stripe integration (Phase 4)
    stripe_subscription_id = Column(String, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="license")
    tier = relationship("LicenseTier", back_populates="licenses")
    
    @property
    def is_trial(self) -> bool:
        """Check if license is in trial period"""
        if not self.trial_ends_at:
            return False
        return datetime.utcnow() < self.trial_ends_at
    
    @property
    def is_expired(self) -> bool:
        """Check if license is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def days_until_expiry(self) -> int:
        """Get days until expiry"""
        if not self.expires_at:
            return -1
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    def __repr__(self):
        return f"<License user_id={self.user_id} tier={self.tier_id} status={self.status}>"

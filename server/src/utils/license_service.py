"""
License Service

Business logic for license management
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Tuple

from ..models import User, License, LicenseTier, ProxyDevice, Printer


class LicenseService:
    """License management service"""
    
    @staticmethod
    def create_free_license(db: Session, user: User) -> License:
        """
        Create a free license for a new user with 14-day Pro trial
        
        Args:
            db: Database session
            user: User to create license for
        
        Returns:
            Created License object
        """
        license = License(
            user_id=user.id,
            tier_id='free',
            status='trial',  # Start in trial status
            starts_at=datetime.utcnow(),
            expires_at=None,  # Free tier doesn't expire
            trial_ends_at=datetime.utcnow() + timedelta(days=14)  # 14-day Pro trial
        )
        
        db.add(license)
        db.commit()
        db.refresh(license)
        
        return license
    
    @staticmethod
    def get_effective_tier(license: License) -> str:
        """
        Get the effective tier ID (considering trial)
        
        During trial, user gets Pro features even on Free license
        
        Args:
            license: License object
        
        Returns:
            Effective tier ID ('free', 'maker', 'pro', 'enterprise')
        """
        if license.is_trial:
            return 'pro'  # Trial users get Pro features
        return license.tier_id
    
    @staticmethod
    def check_device_limit(db: Session, user: User) -> Tuple[bool, int, int]:
        """
        Check if user can add another device
        
        Args:
            db: Database session
            user: User to check
        
        Returns:
            Tuple of (can_add: bool, current_count: int, max_allowed: int)
        """
        if not user.license:
            return False, 0, 0
        
        # Get effective tier
        tier_id = LicenseService.get_effective_tier(user.license)
        tier = db.query(LicenseTier).filter(LicenseTier.id == tier_id).first()
        
        if not tier:
            return False, 0, 0
        
        # Count current devices
        current_count = db.query(ProxyDevice).filter(
            ProxyDevice.user_id == user.id,
            ProxyDevice.status == 'active'
        ).count()
        
        can_add = current_count < tier.max_devices
        
        return can_add, current_count, tier.max_devices
    
    @staticmethod
    def check_printer_limit(db: Session, user: User) -> Tuple[bool, int, int]:
        """
        Check if user can add another printer
        
        Args:
            db: Database session
            user: User to check
        
        Returns:
            Tuple of (can_add: bool, current_count: int, max_allowed: int)
        """
        if not user.license:
            return False, 0, 0
        
        # Get effective tier
        tier_id = LicenseService.get_effective_tier(user.license)
        tier = db.query(LicenseTier).filter(LicenseTier.id == tier_id).first()
        
        if not tier:
            return False, 0, 0
        
        # Count current printers
        current_count = db.query(Printer).filter(
            Printer.user_id == user.id
        ).count()
        
        # -1 means unlimited
        if tier.max_printers == -1:
            return True, current_count, -1
        
        can_add = current_count < tier.max_printers
        
        return can_add, current_count, tier.max_printers
    
    @staticmethod
    def get_history_retention_days(db: Session, user: User) -> int:
        """
        Get history retention days for user
        
        Args:
            db: Database session
            user: User to check
        
        Returns:
            Number of days of history to retain (-1 for unlimited)
        """
        if not user.license:
            return 7  # Default fallback
        
        # Get effective tier
        tier_id = LicenseService.get_effective_tier(user.license)
        tier = db.query(LicenseTier).filter(LicenseTier.id == tier_id).first()
        
        if not tier:
            return 7
        
        return tier.history_days

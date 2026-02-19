"""
Admin Routes

Administrative endpoints for managing the platform
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List

from ..database import get_db
from ..models import User, License, LicenseTier, ProxyDevice, Printer
from ..schemas.admin import UserAdminView, SystemStats, LicenseUpdate
from ..auth.dependencies import get_current_admin

router = APIRouter()


@router.get("/users", response_model=List[UserAdminView])
def list_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    List all users with their license and usage info
    """
    users = db.query(User).offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        # Count devices and printers
        device_count = db.query(ProxyDevice).filter(
            ProxyDevice.user_id == user.id,
            ProxyDevice.status == 'active'
        ).count()
        
        printer_count = db.query(Printer).filter(
            Printer.user_id == user.id
        ).count()
        
        # Get license info
        license = user.license
        
        user_view = UserAdminView(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_admin=user.is_admin,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            license_tier=license.tier_id if license else 'none',
            license_status=license.status if license else 'none',
            trial_ends_at=license.trial_ends_at if license else None,
            device_count=device_count,
            printer_count=printer_count
        )
        
        result.append(user_view)
    
    return result


@router.get("/stats", response_model=SystemStats)
def get_system_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Get system-wide statistics
    """
    # User counts
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    trial_users = db.query(License).filter(
        License.status == 'trial',
        License.trial_ends_at > datetime.utcnow()
    ).count()
    
    paying_users = db.query(License).filter(
        License.tier_id.in_(['maker', 'pro', 'enterprise']),
        License.status == 'active'
    ).count()
    
    # Device counts
    total_devices = db.query(ProxyDevice).count()
    active_devices = db.query(ProxyDevice).filter(
        ProxyDevice.status == 'active'
    ).count()
    
    # Printer count
    total_printers = db.query(Printer).count()
    
    # Revenue calculation
    license_counts = db.query(
        License.tier_id,
        func.count(License.id)
    ).filter(
        License.status == 'active',
        License.tier_id.in_(['maker', 'pro', 'enterprise'])
    ).group_by(License.tier_id).all()
    
    tier_prices = {
        'maker': 1000,      # $10
        'pro': 5000,        # $50
        'enterprise': 15000 # $150
    }
    
    revenue_monthly = sum(
        tier_prices.get(tier, 0) * count 
        for tier, count in license_counts
    )
    
    # Assume 17% discount for yearly (matching our pricing)
    revenue_yearly = int(revenue_monthly * 12 * 0.83)
    
    # Recent signups
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_signups = db.query(User).filter(
        User.created_at >= seven_days_ago
    ).count()
    
    # Trials expiring soon
    seven_days_future = datetime.utcnow() + timedelta(days=7)
    trials_expiring = db.query(License).filter(
        License.status == 'trial',
        License.trial_ends_at <= seven_days_future,
        License.trial_ends_at > datetime.utcnow()
    ).count()
    
    return SystemStats(
        total_users=total_users,
        active_users=active_users,
        trial_users=trial_users,
        paying_users=paying_users,
        total_devices=total_devices,
        active_devices=active_devices,
        total_printers=total_printers,
        revenue_monthly=revenue_monthly,
        revenue_yearly=revenue_yearly,
        recent_signups_7d=recent_signups,
        trials_expiring_7d=trials_expiring
    )


@router.get("/users/{user_id}", response_model=UserAdminView)
def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Get detailed info about a specific user
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    device_count = db.query(ProxyDevice).filter(
        ProxyDevice.user_id == user.id,
        ProxyDevice.status == 'active'
    ).count()
    
    printer_count = db.query(Printer).filter(
        Printer.user_id == user.id
    ).count()
    
    license = user.license
    
    return UserAdminView(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        license_tier=license.tier_id if license else 'none',
        license_status=license.status if license else 'none',
        trial_ends_at=license.trial_ends_at if license else None,
        device_count=device_count,
        printer_count=printer_count
    )


@router.patch("/users/{user_id}/license")
def update_user_license(
    user_id: int,
    license_update: LicenseUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Manually update a user's license tier
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or license not found"
        )
    
    # Verify tier exists
    tier = db.query(LicenseTier).filter(
        LicenseTier.id == license_update.tier_id
    ).first()
    
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tier ID"
        )
    
    # Update license
    license = user.license
    license.tier_id = license_update.tier_id
    
    if license_update.status:
        license.status = license_update.status
    
    license.updated_at = datetime.utcnow()
    
    db.commit()
    
    print(f"✓ Admin {admin.email} updated license for user {user.email} → {license_update.tier_id}")
    
    return {
        "message": "License updated successfully",
        "user_id": user_id,
        "new_tier": license_update.tier_id,
        "status": license.status
    }


@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Deactivate a user account
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()
    
    print(f"✓ Admin {admin.email} deactivated user {user.email}")
    
    return {"message": "User deactivated successfully"}


@router.post("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    """
    Activate a user account
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    user.updated_at = datetime.utcnow()
    db.commit()
    
    print(f"✓ Admin {admin.email} activated user {user.email}")
    
    return {"message": "User activated successfully"}

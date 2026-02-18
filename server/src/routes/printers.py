"""
Printer Routes

Printer registration and management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from ..database import get_db
from ..models import User, ProxyDevice, Printer
from ..schemas import PrinterCreate, PrinterUpdate, PrinterResponse
from ..auth.dependencies import get_current_user, get_current_device
from ..utils.license_service import LicenseService

router = APIRouter()


@router.post("", response_model=PrinterResponse, status_code=status.HTTP_201_CREATED)
def register_printer(
    printer_data: PrinterCreate,
    db: Session = Depends(get_db),
    current_device: ProxyDevice = Depends(get_current_device)
):
    """
    Register a printer (called by proxy device)
    
    Enforces printer limit based on user's license tier
    """
    # Get the user (device owner)
    user = db.query(User).filter(User.id == current_device.user_id).first()
    
    # Check if printer already exists for this device
    existing = db.query(Printer).filter(
        Printer.ip == printer_data.ip,
        Printer.device_id == current_device.id
    ).first()
    
    if existing:
        # Update existing printer info (doesn't count against limit)
        existing.name = printer_data.name
        existing.location = printer_data.location
        existing.model = printer_data.model
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        
        print(f"✓ Updated existing printer: {existing.name} ({existing.ip})")
        
        return existing
    
    # Check printer limit before creating new printer
    can_add, current_count, max_allowed = LicenseService.check_printer_limit(db, user)
    
    if not can_add:
        tier_id = LicenseService.get_effective_tier(user.license)
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Printer limit reached. Your {tier_id} plan allows {max_allowed} printer(s). You have {current_count}. Please upgrade to add more printers."
        )
    
    # Create new printer
    printer = Printer(
        user_id=current_device.user_id,
        device_id=current_device.id,
        ip=printer_data.ip,
        name=printer_data.name,
        location=printer_data.location,
        model=printer_data.model,
        manufacturer=printer_data.manufacturer,
        connection_status="connected"
    )
    
    db.add(printer)
    db.commit()
    db.refresh(printer)
    
    print(f"✓ Printer registered: {printer.name} ({printer.ip})")
    print(f"  → Printer count: {current_count + 1}/{max_allowed if max_allowed != -1 else '∞'}")
    
    return printer


@router.get("", response_model=List[PrinterResponse])
def list_printers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all printers for current user"""
    printers = db.query(Printer).filter(
        Printer.user_id == current_user.id
    ).all()
    
    return printers


@router.get("/{printer_id}", response_model=PrinterResponse)
def get_printer(
    printer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific printer by ID"""
    printer = db.query(Printer).filter(
        Printer.id == printer_id,
        Printer.user_id == current_user.id
    ).first()
    
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found"
        )
    
    return printer


@router.patch("/{printer_id}", response_model=PrinterResponse)
def update_printer(
    printer_id: int,
    printer_data: PrinterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a printer"""
    printer = db.query(Printer).filter(
        Printer.id == printer_id,
        Printer.user_id == current_user.id
    ).first()
    
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found"
        )
    
    # Update fields if provided
    if printer_data.name is not None:
        printer.name = printer_data.name
    if printer_data.location is not None:
        printer.location = printer_data.location
    if printer_data.model is not None:
        printer.model = printer_data.model
    
    printer.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(printer)
    
    return printer


@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_printer(
    printer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a printer and all its metrics"""
    printer = db.query(Printer).filter(
        Printer.id == printer_id,
        Printer.user_id == current_user.id
    ).first()
    
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found"
        )
    
    db.delete(printer)
    db.commit()
    
    print(f"✓ Printer deleted: {printer.name}")

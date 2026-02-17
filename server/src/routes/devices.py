"""
Device Routes

Proxy device registration and management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from ..database import get_db
from ..models import User, ProxyDevice
from ..schemas import DeviceCreate, DeviceResponse, DeviceRegistrationResponse
from ..auth.dependencies import get_current_user

router = APIRouter()


@router.post("/register", response_model=DeviceRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_device(
    device_data: DeviceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a new proxy device
    Returns the device API key (only shown once!)
    """
    # Check if device with same hardware_id already exists
    if device_data.hardware_id:
        existing = db.query(ProxyDevice).filter(
            ProxyDevice.hardware_id == device_data.hardware_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device with this hardware ID already registered"
            )
    
    # Generate API key
    api_key = ProxyDevice.generate_api_key()
    
    # Create device
    device = ProxyDevice(
        user_id=current_user.id,
        name=device_data.name,
        api_key=api_key,
        hardware_id=device_data.hardware_id,
        version=device_data.version,
        status="active",
        ip_address=request.client.host
    )
    
    db.add(device)
    db.commit()
    db.refresh(device)
    
    print(f"✓ Device registered: {device.name} for user {current_user.email}")
    
    return device


@router.get("", response_model=List[DeviceResponse])
def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all proxy devices for current user
    """
    devices = db.query(ProxyDevice).filter(
        ProxyDevice.user_id == current_user.id
    ).all()
    
    return devices


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific device by ID
    """
    device = db.query(ProxyDevice).filter(
        ProxyDevice.id == device_id,
        ProxyDevice.user_id == current_user.id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a proxy device
    """
    device = db.query(ProxyDevice).filter(
        ProxyDevice.id == device_id,
        ProxyDevice.user_id == current_user.id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    db.delete(device)
    db.commit()
    
    print(f"✓ Device deleted: {device.name}")

"""
Metrics Routes

Printer metrics ingestion and query endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional

from ..database import get_db
from ..models import User, ProxyDevice, Printer, PrinterMetrics
from ..schemas import MetricsIngest, MetricsResponse, MetricsSummary
from ..auth.dependencies import get_current_user, get_current_device

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
def ingest_metrics(
    metrics_data: MetricsIngest,
    db: Session = Depends(get_db),
    current_device: ProxyDevice = Depends(get_current_device)
):
    """
    Ingest printer metrics from proxy device
    Requires device API key authentication
    """
    # Find printer by IP address for this device
    printer = db.query(Printer).filter(
        Printer.ip == metrics_data.printer_id,
        Printer.device_id == current_device.id
    ).first()
    
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Printer {metrics_data.printer_id} not registered for this device"
        )
    
    # Create metrics record
    metrics = PrinterMetrics(
        printer_id=printer.id,
        timestamp=metrics_data.timestamp or datetime.utcnow(),
        total_pages=metrics_data.metrics.total_pages,
        toner_level_pct=metrics_data.metrics.toner_level_pct,
        toner_status=metrics_data.metrics.toner_status,
        drum_level_pct=metrics_data.metrics.drum_level_pct,
        device_status=metrics_data.metrics.device_status,
        model=metrics_data.metrics.model
    )
    
    db.add(metrics)
    
    # Update printer last seen and status
    printer.last_seen_at = datetime.utcnow()
    printer.connection_status = "connected"
    if metrics_data.metrics.model:
        printer.model = metrics_data.metrics.model
    
    # Update device last seen
    current_device.last_seen_at = datetime.utcnow()
    
    db.commit()
    
    print(f"✓ Metrics ingested for {printer.name} ({printer.ip})")
    
    return {
        "message": "Metrics ingested successfully",
        "printer_id": printer.id,
        "timestamp": metrics.timestamp
    }


@router.get("/summary", response_model=List[MetricsSummary])
def get_metrics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get latest metrics summary for all printers
    """
    printers = db.query(Printer).filter(
        Printer.user_id == current_user.id
    ).all()
    
    summaries = []
    
    for printer in printers:
        # Get LATEST metrics using max timestamp
        latest = db.query(PrinterMetrics).filter(
            PrinterMetrics.printer_id == printer.id
        ).order_by(PrinterMetrics.timestamp.desc()).first()
        
        summary = MetricsSummary(
            printer_id=printer.id,
            printer_name=printer.name,
            printer_ip=printer.ip,
            location=printer.location,
            connection_status=printer.connection_status,
            latest_timestamp=latest.timestamp if latest else None,
            total_pages=latest.total_pages if latest else None,
            toner_level_pct=latest.toner_level_pct if latest else None,
            toner_status=latest.toner_status if latest else None,
            drum_level_pct=latest.drum_level_pct if latest else None
        )
        
        summaries.append(summary)
    
    return summaries


@router.get("/{printer_id}", response_model=List[MetricsResponse])
def get_printer_metrics(
    printer_id: int,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get metrics history for a specific printer
    Returns most recent first
    """
    # Verify printer ownership
    printer = db.query(Printer).filter(
        Printer.id == printer_id,
        Printer.user_id == current_user.id
    ).first()
    
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Printer not found"
        )
    
    # Get metrics for specified period, LATEST FIRST
    since = datetime.utcnow() - timedelta(days=days)
    
    metrics = db.query(PrinterMetrics).filter(
        PrinterMetrics.printer_id == printer_id,
        PrinterMetrics.timestamp >= since
    ).order_by(PrinterMetrics.timestamp.desc()).all()
    
    return metrics

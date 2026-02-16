"""
Monitoring Collector

Collects metrics from printers using SNMP.
This is your existing, proven code from printer_monitor.py
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from utils.snmp import (
    snmp_get,
    get_supply_info,
    calculate_toner_percentage,
    PrinterOIDs
)


async def get_printer_metrics_async(ip: str) -> Optional[Dict[str, Any]]:
    """
    Get all metrics for a printer asynchronously
    
    Args:
        ip: IP address of the printer
    
    Returns:
        Dictionary with metrics or None if failed
    """
    print(f"\nQuerying printer at {ip}...")
    
    metrics = {
        'total_pages': None,
        'model': None,
        'device_status': None,
        'toner_level_pct': None,
        'toner_status': None,
        'drum_level_pct': None,
    }
    
    # Get basic info
    total_pages = await snmp_get(ip, PrinterOIDs.TOTAL_PAGES)
    if total_pages:
        try:
            metrics['total_pages'] = int(total_pages)
            print(f"  Total Pages: {total_pages}")
        except ValueError:
            pass
    
    model = await snmp_get(ip, PrinterOIDs.MODEL)
    if model:
        metrics['model'] = model
        print(f"  Model: {model}")
    
    device_status = await snmp_get(ip, PrinterOIDs.DEVICE_STATUS)
    if device_status:
        try:
            metrics['device_status'] = int(device_status)
        except ValueError:
            pass
    
    # Get supply information
    # Check first few indices for toner and drum
    for index in range(1, 10):
        supply = await get_supply_info(ip, index)
        if not supply:
            continue
        
        desc = supply.get('description', '').lower()
        current = supply.get('current_level')
        max_cap = supply.get('max_capacity')
        
        if not current or not max_cap:
            continue
        
        # Check if this is toner
        if 'toner' in desc and 'black' in desc:
            pct, status = await calculate_toner_percentage(current, max_cap)
            if pct is not None:
                metrics['toner_level_pct'] = pct
                print(f"  Black Toner: {pct}%")
            elif status:
                metrics['toner_status'] = status
                print(f"  Black Toner: {status}")
        
        # Check if this is drum
        elif 'drum' in desc:
            pct, status = await calculate_toner_percentage(current, max_cap)
            if pct is not None:
                metrics['drum_level_pct'] = pct
                print(f"  Drum Unit: {pct}%")
    
    return metrics if any(v is not None for v in metrics.values()) else None


def get_printer_metrics(ip: str) -> Optional[Dict[str, Any]]:
    """
    Synchronous wrapper for async get_printer_metrics
    
    Args:
        ip: IP address of printer
    
    Returns:
        Dictionary with metrics or None if failed
    """
    try:
        return asyncio.run(get_printer_metrics_async(ip))
    except Exception as e:
        print(f"  Error getting metrics: {e}")
        return None


async def monitor_printer(ip: str, storage) -> bool:
    """
    Monitor a single printer and save metrics
    
    Args:
        ip: IP address of printer
        storage: Storage backend instance
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get metrics from printer
        metrics = await get_printer_metrics_async(ip)
        
        if metrics:
            # Add timestamp
            metrics['timestamp'] = datetime.now()
            
            # Save metrics
            success = storage.save_metrics(ip, metrics)
            
            if success:
                print(f"✓ Metrics saved for {ip}")
                return True
            else:
                print(f"✗ Failed to save metrics for {ip}")
                return False
        else:
            print(f"✗ Failed to get metrics for {ip}")
            return False
            
    except Exception as e:
        print(f"✗ Error monitoring {ip}: {e}")
        return False


async def monitor_multiple_printers(printers: list, storage) -> Dict[str, bool]:
    """
    Monitor multiple printers concurrently
    
    Args:
        printers: List of printer dictionaries with 'ip' key
        storage: Storage backend instance
    
    Returns:
        Dictionary mapping printer IPs to success status
    """
    tasks = []
    
    for printer in printers:
        ip = printer.get('ip') if isinstance(printer, dict) else printer
        tasks.append(monitor_printer(ip, storage))
    
    results = await asyncio.gather(*tasks)
    
    # Map results back to IPs
    status = {}
    for i, printer in enumerate(printers):
        ip = printer.get('ip') if isinstance(printer, dict) else printer
        status[ip] = results[i]
    
    return status

"""
SNMP Utilities

Core SNMP functions for querying printers.
This is your existing, proven code from printer_monitor.py
"""

import asyncio
import sys

try:
    import pysnmp.hlapi.asyncio as hlapi
except ImportError:
    print("Error: pysnmp library not installed")
    print("Install with: pip install pysnmp")
    sys.exit(1)

from config.settings import Config


async def snmp_get(ip: str, oid: str, timeout: int = None) -> str:
    """
    Query a single SNMP OID from a device using async API
    
    Args:
        ip: IP address of the printer
        oid: SNMP OID to query
        timeout: Timeout in seconds (uses Config.SNMP_TIMEOUT if not specified)
    
    Returns:
        Value if successful, None otherwise
    """
    if timeout is None:
        timeout = Config.SNMP_TIMEOUT
    
    try:
        snmpEngine = hlapi.SnmpEngine()
        errorIndication, errorStatus, errorIndex, varBinds = await hlapi.getCmd(
            snmpEngine,
            hlapi.CommunityData(Config.SNMP_COMMUNITY, mpModel=0),
            hlapi.UdpTransportTarget((ip, Config.SNMP_PORT), timeout=timeout),
            hlapi.ContextData(),
            hlapi.ObjectType(hlapi.ObjectIdentity(oid))
        )
        
        if errorIndication:
            return None
        elif errorStatus:
            return None
        else:
            value = str(varBinds[0][1])
            if "No Such" not in value and value.strip():
                return value
            return None
    except Exception:
        return None


async def get_supply_info(ip: str, index: int) -> dict:
    """
    Get supply information for a specific index
    
    Args:
        ip: IP address of printer
        index: Supply index number (1-10)
    
    Returns:
        Dictionary with supply info or None
    """
    base_oids = {
        'description': f'1.3.6.1.2.1.43.11.1.1.6.1.{index}',
        'type': f'1.3.6.1.2.1.43.11.1.1.5.1.{index}',
        'unit': f'1.3.6.1.2.1.43.11.1.1.7.1.{index}',
        'max_capacity': f'1.3.6.1.2.1.43.11.1.1.8.1.{index}',
        'current_level': f'1.3.6.1.2.1.43.11.1.1.9.1.{index}',
    }
    
    supply = {}
    for key, oid in base_oids.items():
        value = await snmp_get(ip, oid)
        if value:
            supply[key] = value
    
    return supply if supply else None


async def calculate_toner_percentage(current: str, max_capacity: str) -> tuple:
    """
    Calculate toner percentage from current and max values
    
    Args:
        current: Current level value
        max_capacity: Maximum capacity value
    
    Returns:
        Tuple of (percentage: int or None, status: str or None)
    """
    try:
        current_val = int(current)
        max_val = int(max_capacity)
        
        # Handle special values
        if current_val == -3:
            return None, "OK"  # Toner OK but level not reported
        elif current_val == -2:
            return None, "Unknown"
        elif current_val < 0:
            return None, f"Status: {current_val}"
        
        # Calculate percentage if we have valid values
        if max_val > 0 and max_val != -2:
            percentage = int((current_val / max_val) * 100)
            return percentage, None
        
        return None, "Cannot calculate"
        
    except (ValueError, ZeroDivisionError):
        return None, "Error"


# Common SNMP OIDs for printers
class PrinterOIDs:
    """Common SNMP OIDs for printer information"""
    
    # System information
    SYS_DESCR = '1.3.6.1.2.1.1.1.0'
    SYS_NAME = '1.3.6.1.2.1.1.5.0'
    
    # Printer info
    MODEL = '1.3.6.1.2.1.25.3.2.1.3.1'
    DEVICE_STATUS = '1.3.6.1.2.1.25.3.2.1.5.1'
    
    # Page counts
    TOTAL_PAGES = '1.3.6.1.2.1.43.10.2.1.4.1.1'
    
    # Supply info (requires index)
    SUPPLY_DESCRIPTION = '1.3.6.1.2.1.43.11.1.1.6.1'  # + .{index}
    SUPPLY_TYPE = '1.3.6.1.2.1.43.11.1.1.5.1'  # + .{index}
    SUPPLY_MAX_CAPACITY = '1.3.6.1.2.1.43.11.1.1.8.1'  # + .{index}
    SUPPLY_CURRENT_LEVEL = '1.3.6.1.2.1.43.11.1.1.9.1'  # + .{index}

"""
Subnet Scanner

Scans configured remote subnets for SNMP-enabled printers
"""

import ipaddress
from typing import List, Tuple
from pysnmp.hlapi import *
from config.settings import Config

config = Config()


def scan_subnet(subnet_cidr: str) -> List[str]:
    """
    Scan a subnet for SNMP-enabled devices
    
    Args:
        subnet_cidr: Subnet in CIDR notation (e.g., "192.168.2.0/24")
    
    Returns:
        List of IP addresses that respond to SNMP
    """
    print(f"  Scanning subnet: {subnet_cidr}")
    
    try:
        network = ipaddress.ip_network(subnet_cidr, strict=False)
    except ValueError as e:
        print(f"  ✗ Invalid subnet: {e}")
        return []
    
    discovered_ips = []
    total_hosts = network.num_addresses - 2  # Exclude network and broadcast
    
    # Limit scan to reasonable size
    if total_hosts > 254:
        print(f"  ⚠ Large subnet ({total_hosts} hosts), scanning first 254 IPs only")
        hosts = list(network.hosts())[:254]
    else:
        hosts = list(network.hosts())
    
    print(f"  Scanning {len(hosts)} hosts...")
    
    for i, ip in enumerate(hosts, 1):
        ip_str = str(ip)
        
        # Quick SNMP check - try to get sysDescr
        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(config.SNMP_COMMUNITY),
                UdpTransportTarget((ip_str, config.SNMP_PORT), timeout=0.5, retries=0),
                ContextData(),
                ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
            )
            
            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
            
            if not errorIndication and not errorStatus:
                print(f"  ✓ Found SNMP device at {ip_str}")
                discovered_ips.append(ip_str)
        except Exception:
            pass  # Silently skip non-responsive IPs
        
        # Progress indicator every 50 hosts
        if i % 50 == 0:
            print(f"    Progress: {i}/{len(hosts)} hosts scanned, {len(discovered_ips)} found")
    
    print(f"  ✓ Scan complete: {len(discovered_ips)} SNMP devices found")
    return discovered_ips


def check_if_printer(ip: str) -> bool:
    """
    Check if an SNMP device is a printer
    
    Args:
        ip: IP address to check
    
    Returns:
        True if device appears to be a printer
    """
    try:
        # Try to get printer-specific OIDs
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(config.SNMP_COMMUNITY),
            UdpTransportTarget((ip, config.SNMP_PORT), timeout=1),
            ContextData(),
            # Printer MIB - device type
            ObjectType(ObjectIdentity('1.3.6.1.2.1.25.3.2.1.2.1'))
        )
        
        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
        
        if not errorIndication and not errorStatus:
            # If we can read printer MIB, it's likely a printer
            return True
            
    except Exception:
        pass
    
    return False


def scan_and_filter_printers(subnet_cidr: str) -> List[str]:
    """
    Scan subnet and return only printer IPs
    
    Args:
        subnet_cidr: Subnet to scan
    
    Returns:
        List of printer IP addresses
    """
    # First, find all SNMP devices
    snmp_devices = scan_subnet(subnet_cidr)
    
    if not snmp_devices:
        return []
    
    print(f"  Filtering for printers...")
    printers = []
    
    for ip in snmp_devices:
        if check_if_printer(ip):
            print(f"    ✓ {ip} is a printer")
            printers.append(ip)
    
    print(f"  ✓ Found {len(printers)} printer(s)")
    return printers

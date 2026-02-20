"""
PrinterMonitor Pro - Proxy Main Entry Point
"""

import sys
import time
from datetime import datetime
from config.settings import Config
from storage import get_storage
from monitoring.collector import monitor_multiple_printers
from discovery.subnet_scanner import scan_and_filter_printers

config = Config()


def print_banner():
    """Print startup banner"""
    print("=" * 80)
    print("PRINTERMONITOR PRO - PROXY DEVICE")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


def scan_remote_subnets_if_needed(storage):
    """
    Check for configured remote subnets and scan them for new printers
    """
    if config.MONITOR_MODE != "cloud":
        return  # Only works in cloud mode
    
    try:
        # Get configured subnets from cloud
        response = storage.session.get(
            f"{storage.api_url}/remote-subnets",
            headers=storage.headers
        )
        
        if response.status_code != 200:
            return
        
        subnets = response.json()
        enabled_subnets = [s for s in subnets if s.get('enabled', True)]
        
        if not enabled_subnets:
            return
        
        print("\n" + "=" * 80)
        print("SCANNING REMOTE SUBNETS")
        print("=" * 80)
        
        for subnet_config in enabled_subnets:
            subnet = subnet_config['subnet']
            description = subnet_config.get('description', 'No description')
            
            print(f"\nSubnet: {subnet}")
            print(f"Description: {description}")
            
            # Scan for printers
            printer_ips = scan_and_filter_printers(subnet)
            
            # Register any new printers
            for ip in printer_ips:
                try:
                    # Check if printer already exists
                    existing = storage.session.get(
                        f"{storage.api_url}/printers",
                        headers=storage.headers
                    ).json()
                    
                    if any(p['ip'] == ip for p in existing):
                        print(f"  → {ip} already registered")
                        continue
                    
                    # Register new printer
                    response = storage.session.post(
                        f"{storage.api_url}/printers",
                        headers=storage.headers,
                        json={
                            "ip": ip,
                            "name": f"Printer at {ip}",
                            "location": f"Subnet {subnet}",
                            "model": "Auto-discovered"
                        }
                    )
                    
                    if response.status_code == 201:
                        print(f"  ✓ Registered new printer: {ip}")
                    else:
                        print(f"  ✗ Failed to register {ip}: {response.text}")
                        
                except Exception as e:
                    print(f"  ✗ Error registering {ip}: {e}")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"Error scanning remote subnets: {e}")


def main():
    """Main entry point"""
    print_banner()
    
    storage = get_storage()
    
    # Get command
    command = sys.argv[1] if len(sys.argv) > 1 else "once"
    
    if command == "once":
        # Run once: scan subnets + monitor printers
        scan_remote_subnets_if_needed(storage)
        printers = storage.get_printers()
        
        if printers:
            print(f"\n✓ Monitoring {len(printers)} printer(s)")
            monitor_multiple_printers(printers, storage)
        else:
            print("\n⏸  No printers to monitor")
            
    elif command == "loop":
        # Continuous loop
        print("\nStarting continuous monitoring...")
        print(f"Check interval: {config.MONITOR_INTERVAL} seconds")
        print("Press Ctrl+C to stop\n")
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                print(f"\n{'=' * 80}")
                print(f"CYCLE {cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 80)
                
                # Scan subnets every 10 cycles (or ~50 minutes with 5min interval)
                if cycle % 10 == 1:
                    scan_remote_subnets_if_needed(storage)
                
                # Monitor known printers
                printers = storage.get_printers()
                
                if printers:
                    print(f"Monitoring {len(printers)} printer(s)...")
                    monitor_multiple_printers(printers, storage)
                else:
                    print("No printers registered yet")
                
                print(f"\nNext check in {config.MONITOR_INTERVAL} seconds...")
                time.sleep(config.MONITOR_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\nStopping monitoring...")
            
    else:
        print("Usage: python main.py [once|loop]")
        sys.exit(1)


if __name__ == "__main__":
    main()

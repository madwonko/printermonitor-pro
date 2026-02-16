"""
PrinterMonitor Pro - Proxy Main Entry Point

This is the main script that runs on the local network device (Raspberry Pi, Linux server, etc.)
to monitor printers and send data to the configured storage backend (local or cloud).
"""

import sys
import asyncio
import time
from datetime import datetime

from config.settings import Config
from storage import get_storage
from monitoring.collector import monitor_multiple_printers


def main():
    """Main entry point"""
    
    print("="*80)
    print("PRINTERMONITOR PRO - PROXY DEVICE")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Display configuration
    Config.display()
    print()
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease check your .env file or environment variables")
        return 1
    
    # Get storage backend
    try:
        storage = get_storage()
    except Exception as e:
        print(f"✗ Failed to initialize storage: {e}")
        return 1
    
    # Health check
    print("\nPerforming health check...")
    if not storage.health_check():
        print("✗ Storage backend is not healthy!")
        return 1
    print("✓ Storage backend is healthy")
    
    # Get list of printers
    print("\nGetting list of printers...")
    printers = storage.get_printers()
    
    if not printers:
        print("\n⚠ No printers found in storage!")
        print("\nTo add printers:")
        print("  1. Run printer discovery: python -m discovery.scanner")
        print("  2. Or manually register printers in the database/cloud")
        return 0
    
    print(f"✓ Found {len(printers)} printer(s) to monitor")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "once":
            # Single monitoring run
            print("\n" + "="*80)
            print("STARTING MONITORING CYCLE")
            print("="*80)
            
            run_monitoring_cycle(storage, printers)
            
        elif command == "loop":
            # Continuous monitoring
            interval = Config.MONITOR_INTERVAL
            if len(sys.argv) > 2:
                try:
                    interval = int(sys.argv[2])
                except ValueError:
                    print(f"Invalid interval: {sys.argv[2]}")
                    return 1
            
            print(f"\n✓ Starting continuous monitoring (interval: {interval} seconds)")
            print("Press Ctrl+C to stop\n")
            
            try:
                while True:
                    print("="*80)
                    print(f"MONITORING CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print("="*80)
                    
                    run_monitoring_cycle(storage, printers)
                    
                    print(f"\nSleeping for {interval} seconds...")
                    print("="*80)
                    print()
                    time.sleep(interval)
                    
            except KeyboardInterrupt:
                print("\n\n✓ Monitoring stopped by user")
                return 0
        
        else:
            print(f"Unknown command: {command}")
            print_usage()
            return 1
    else:
        # Default: single run
        print("\n" + "="*80)
        print("STARTING MONITORING CYCLE")
        print("="*80)
        
        run_monitoring_cycle(storage, printers)
    
    return 0


def run_monitoring_cycle(storage, printers):
    """Run a single monitoring cycle"""
    
    # Monitor all printers
    results = asyncio.run(monitor_multiple_printers(printers, storage))
    
    # Print summary
    successful = sum(1 for success in results.values() if success)
    failed = len(results) - successful
    
    print("\n" + "="*80)
    print("MONITORING CYCLE COMPLETE")
    print("="*80)
    print(f"Successful: {successful}/{len(results)}")
    if failed > 0:
        print(f"Failed: {failed}/{len(results)}")
        print("\nFailed printers:")
        for ip, success in results.items():
            if not success:
                print(f"  - {ip}")
    print("="*80)


def print_usage():
    """Print usage instructions"""
    print("""
PrinterMonitor Pro Proxy - Usage:

python src/main.py              Run single monitoring cycle
python src/main.py once         Run single monitoring cycle (explicit)
python src/main.py loop         Continuous monitoring (uses MONITOR_INTERVAL from config)
python src/main.py loop 1800    Continuous monitoring with custom interval (30 minutes)

Configuration:
- Copy .env.example to .env and customize
- Set MONITOR_MODE to 'local' or 'cloud'
- Configure SNMP settings as needed

Examples:
    python src/main.py                    # Single run
    python src/main.py loop               # Continuous with default interval
    python src/main.py loop 900           # Continuous every 15 minutes
    
For discovery and setup:
    python -m discovery.scanner       # Scan network for printers
""")


if __name__ == "__main__":
    sys.exit(main())

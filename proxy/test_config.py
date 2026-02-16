#!/usr/bin/env python3
"""
Test Configuration Script

Quick test to verify the proxy configuration is working correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Config
from storage import get_storage


def main():
    print("="*80)
    print("PRINTERMONITOR PRO - CONFIGURATION TEST")
    print("="*80)
    print()
    
    # Test 1: Display configuration
    print("Test 1: Configuration Display")
    print("-"*80)
    try:
        Config.display()
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return 1
    
    print()
    
    # Test 2: Validate configuration
    print("Test 2: Configuration Validation")
    print("-"*80)
    try:
        Config.validate()
        print("✓ Configuration is valid")
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return 1
    
    print()
    
    # Test 3: Initialize storage
    print("Test 3: Storage Initialization")
    print("-"*80)
    try:
        storage = get_storage()
        print("✓ Storage backend initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize storage: {e}")
        return 1
    
    print()
    
    # Test 4: Storage health check
    print("Test 4: Storage Health Check")
    print("-"*80)
    try:
        if storage.health_check():
            print("✓ Storage backend is healthy")
        else:
            print("✗ Storage backend health check failed")
            return 1
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return 1
    
    print()
    print("="*80)
    print("ALL TESTS PASSED!")
    print("="*80)
    print()
    print("Next steps:")
    print("  1. Copy your printer discovery script to src/discovery/")
    print("  2. Run discovery to find printers")
    print("  3. Test monitoring: python src/main.py once")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

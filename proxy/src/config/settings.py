"""
Configuration settings for PrinterMonitor Pro Proxy

Supports two modes:
- local: Store data in local SQLite database (same as Community Edition)
- cloud: Send data to PrinterMonitor Pro cloud API
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Main configuration class"""
    
    # ============================================================================
    # MODE SELECTION
    # ============================================================================
    
    # Options: 'local' or 'cloud'
    MODE = os.getenv('MONITOR_MODE', 'local')
    
    # ============================================================================
    # SNMP SETTINGS (same for both modes)
    # ============================================================================
    
    SNMP_COMMUNITY = os.getenv('SNMP_COMMUNITY', 'public')
    SNMP_TIMEOUT = int(os.getenv('SNMP_TIMEOUT', '2'))
    SNMP_PORT = int(os.getenv('SNMP_PORT', '161'))
    
    # ============================================================================
    # LOCAL MODE SETTINGS
    # ============================================================================
    
    # SQLite database file (used for local mode OR cloud mode buffering)
    DATABASE_FILE = os.getenv('DATABASE_FILE', 'printer_monitoring.db')
    
    # ============================================================================
    # CLOUD MODE SETTINGS
    # ============================================================================
    
    # Cloud API URL (required for cloud mode)
    CLOUD_API_URL = os.getenv('CLOUD_API_URL', None)
    
    # Cloud API Key (required for cloud mode)
    CLOUD_API_KEY = os.getenv('CLOUD_API_KEY', None)
    
    # Retry settings for cloud API
    CLOUD_RETRY_ATTEMPTS = int(os.getenv('CLOUD_RETRY_ATTEMPTS', '3'))
    CLOUD_RETRY_DELAY = int(os.getenv('CLOUD_RETRY_DELAY', '5'))  # seconds
    
    # Enable local buffering when cloud is unavailable
    CLOUD_ENABLE_BUFFER = os.getenv('CLOUD_ENABLE_BUFFER', 'true').lower() == 'true'
    
    # ============================================================================
    # MONITORING SETTINGS
    # ============================================================================
    
    # How often to check printers (seconds)
    MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', '3600'))  # 1 hour default
    
    # ============================================================================
    # LOGGING
    # ============================================================================
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'proxy.log')
    
    @classmethod
    def validate(cls):
        """Validate configuration based on selected mode"""
        
        if cls.MODE not in ['local', 'cloud']:
            raise ValueError(f"Invalid MODE: {cls.MODE}. Must be 'local' or 'cloud'")
        
        if cls.MODE == 'cloud':
            if not cls.CLOUD_API_URL:
                raise ValueError("CLOUD_API_URL is required when MODE is 'cloud'")
            
            if not cls.CLOUD_API_KEY:
                raise ValueError("CLOUD_API_KEY is required when MODE is 'cloud'")
        
        return True
    
    @classmethod
    def display(cls):
        """Display current configuration (for debugging)"""
        print("="*80)
        print("PRINTERMONITOR PRO - PROXY CONFIGURATION")
        print("="*80)
        print(f"Mode: {cls.MODE}")
        print(f"SNMP Community: {cls.SNMP_COMMUNITY}")
        print(f"SNMP Timeout: {cls.SNMP_TIMEOUT}s")
        print(f"Monitor Interval: {cls.MONITOR_INTERVAL}s")
        
        if cls.MODE == 'local':
            print(f"Database: {cls.DATABASE_FILE}")
        else:
            print(f"Cloud API: {cls.CLOUD_API_URL}")
            print(f"API Key: {cls.CLOUD_API_KEY[:10]}..." if cls.CLOUD_API_KEY else "Not set")
            print(f"Local Buffering: {'Enabled' if cls.CLOUD_ENABLE_BUFFER else 'Disabled'}")
        
        print("="*80)

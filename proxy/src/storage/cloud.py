"""
Cloud Storage Backend - API Client

Sends printer data to PrinterMonitor Pro cloud API.
Includes retry logic and optional local buffering when cloud is unavailable.
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import time

from .interface import StorageBackend
from .local import LocalStorage


class CloudStorage(StorageBackend):
    """Cloud API storage backend"""
    
    def __init__(
        self, 
        api_url: str, 
        api_key: str,
        retry_attempts: int = 3,
        retry_delay: int = 5,
        enable_buffer: bool = True
    ):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.enable_buffer = enable_buffer
        
        # Initialize local buffer if enabled
        self.buffer = LocalStorage() if enable_buffer else None
        
        # HTTP session with API key header
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'PrinterMonitorPro-Proxy/1.0'
        })
        
        print(f"✓ Cloud storage initialized: {self.api_url}")
        if self.enable_buffer:
            print("✓ Local buffering enabled")
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict = None,
        params: Dict = None
    ) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        url = f"{self.api_url}{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                if method == 'GET':
                    response = self.session.get(url, params=params, timeout=10)
                elif method == 'POST':
                    response = self.session.post(url, json=data, timeout=10)
                elif method == 'PUT':
                    response = self.session.put(url, json=data, timeout=10)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt < self.retry_attempts - 1:
                    print(f"⚠ API request failed (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                    print(f"  Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"✗ API request failed after {self.retry_attempts} attempts: {e}")
                    return None
    
    def save_metrics(self, printer_id: str, metrics: Dict[str, Any]) -> bool:
        """Save printer metrics to cloud API"""
        
        data = {
            'printer_id': printer_id,
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'total_pages': metrics.get('total_pages'),
                'toner_level_pct': metrics.get('toner_level_pct'),
                'toner_status': metrics.get('toner_status'),
                'drum_level_pct': metrics.get('drum_level_pct'),
                'device_status': metrics.get('device_status'),
                'model': metrics.get('model')
            }
        }
        
        result = self._make_request('POST', '/api/v1/metrics', data=data)
        
        if result:
            print(f"✓ Metrics sent to cloud for {printer_id}")
            return True
        else:
            print(f"✗ Failed to send metrics to cloud for {printer_id}")
            if self.buffer:
                print(f"  → Saving to local buffer instead")
                return self.buffer.save_metrics(printer_id, metrics)
            return False
    
    def get_or_create_printer(
        self, 
        ip: str, 
        name: str, 
        location: str = None, 
        model: str = None
    ) -> Optional[str]:
        """Register printer with cloud API"""
        
        data = {
            'ip': ip,
            'name': name,
            'location': location,
            'model': model
        }
        
        result = self._make_request('POST', '/api/v1/printers', data=data)
        
        if result:
            print(f"✓ Registered printer with cloud: {name} ({ip})")
            if self.buffer:
                self.buffer.get_or_create_printer(ip, name, location, model)
            return ip
        else:
            print(f"✗ Failed to register printer with cloud: {name} ({ip})")
            if self.buffer:
                print(f"  → Registering in local buffer instead")
                return self.buffer.get_or_create_printer(ip, name, location, model)
            return None
    
    def get_printers(self) -> List[Dict[str, Any]]:
        """
        Get printers from local buffer only.
        In cloud mode the proxy monitors whatever is in its local config.
        """
        if self.buffer:
            return self.buffer.get_printers()
        return []
    
    def get_printer_by_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get printer by IP from local buffer"""
        if self.buffer:
            return self.buffer.get_printer_by_ip(ip)
        return None
    
    def health_check(self) -> bool:
        """Check if cloud API is available"""
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"✗ Cloud health check failed: {e}")
            return False

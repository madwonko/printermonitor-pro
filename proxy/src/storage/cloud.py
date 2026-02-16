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
        """
        Initialize cloud storage
        
        Args:
            api_url: Base URL of cloud API (e.g., https://api.printermonitor.pro)
            api_key: API key for authentication
            retry_attempts: Number of retry attempts for failed requests
            retry_delay: Delay between retries in seconds
            enable_buffer: Enable local SQLite buffering when cloud unavailable
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.enable_buffer = enable_buffer
        
        # Initialize local buffer if enabled
        self.buffer = LocalStorage() if enable_buffer else None
        
        # HTTP session with auth header
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
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
        """
        Make HTTP request to cloud API with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/api/v1/metrics')
            data: Request body (for POST/PUT)
            params: Query parameters
        
        Returns:
            Response JSON or None if failed
        """
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
                
                # Check response status
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
        
        # Prepare data for API
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
        
        # Try to send to cloud
        result = self._make_request('POST', '/api/v1/status', data=data)
        
        if result:
            print(f"✓ Metrics sent to cloud for {printer_id}")
            return True
        else:
            print(f"✗ Failed to send metrics to cloud for {printer_id}")
            
            # Fall back to local buffer if enabled
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
        
        # Try to register with cloud
        result = self._make_request('POST', '/api/v1/printers', data=data)
        
        if result:
            print(f"✓ Registered printer with cloud: {name} ({ip})")
            
            # Also register in local buffer if enabled
            if self.buffer:
                self.buffer.get_or_create_printer(ip, name, location, model)
            
            return ip
        else:
            print(f"✗ Failed to register printer with cloud: {name} ({ip})")
            
            # Fall back to local buffer if enabled
            if self.buffer:
                print(f"  → Registering in local buffer instead")
                return self.buffer.get_or_create_printer(ip, name, location, model)
            
            return None
    
    def get_printers(self) -> List[Dict[str, Any]]:
        """Get list of printers from cloud API"""
        
        result = self._make_request('GET', '/api/v1/printers')
        
        if result and 'printers' in result:
            return result['printers']
        else:
            print("✗ Failed to get printers from cloud")
            
            # Fall back to local buffer if enabled
            if self.buffer:
                print("  → Using local buffer instead")
                return self.buffer.get_printers()
            
            return []
    
    def get_printer_by_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get printer from cloud API by IP"""
        
        result = self._make_request('GET', f'/api/v1/printers/{ip}')
        
        if result:
            return result
        else:
            # Fall back to local buffer if enabled
            if self.buffer:
                return self.buffer.get_printer_by_ip(ip)
            
            return None
    
    def health_check(self) -> bool:
        """Check if cloud API is available"""
        
        result = self._make_request('GET', '/health')
        return result is not None

"""
Storage Interface - Abstract Base Class

Defines the contract that all storage backends must implement.
This allows the proxy to work with different storage backends (local SQLite, cloud API, etc.)
without changing the core monitoring logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    def save_metrics(self, printer_id: str, metrics: Dict[str, Any]) -> bool:
        """
        Save printer metrics
        
        Args:
            printer_id: Unique identifier for the printer (usually IP address)
            metrics: Dictionary containing metrics data:
                - total_pages: int
                - toner_level_pct: int (0-100) or None
                - toner_status: str or None
                - drum_level_pct: int (0-100) or None
                - device_status: int or None
                - model: str or None
                - timestamp: datetime
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_or_create_printer(
        self, 
        ip: str, 
        name: str, 
        location: str = None, 
        model: str = None
    ) -> Optional[str]:
        """
        Get existing printer or create new one
        
        Args:
            ip: IP address of printer
            name: Display name
            location: Physical location
            model: Printer model
        
        Returns:
            str: Printer ID if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def get_printers(self) -> List[Dict[str, Any]]:
        """
        Get list of all registered printers
        
        Returns:
            List of printer dictionaries with keys:
                - id, ip, name, location, model, first_seen
        """
        pass
    
    @abstractmethod
    def get_printer_by_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """
        Get printer information by IP address
        
        Args:
            ip: IP address
        
        Returns:
            Printer dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if storage backend is available and healthy
        
        Returns:
            bool: True if healthy, False otherwise
        """
        pass

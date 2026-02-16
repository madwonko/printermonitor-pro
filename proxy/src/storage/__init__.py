"""
Storage Package

Provides different storage backends for printer metrics.
"""

from .factory import get_storage
from .interface import StorageBackend
from .local import LocalStorage
from .cloud import CloudStorage

__all__ = ['get_storage', 'StorageBackend', 'LocalStorage', 'CloudStorage']

"""
Storage Factory

Factory function to get the appropriate storage backend based on configuration.
"""

from .interface import StorageBackend
from .local import LocalStorage
from .cloud import CloudStorage
from config.settings import Config


def get_storage() -> StorageBackend:
    """
    Get storage backend based on configuration
    
    Returns:
        StorageBackend instance (LocalStorage or CloudStorage)
    
    Raises:
        ValueError: If configuration is invalid
    """
    
    # Validate configuration first
    Config.validate()
    
    if Config.MODE == 'local':
        print(f"Using local storage mode: {Config.DATABASE_FILE}")
        return LocalStorage(database_file=Config.DATABASE_FILE)
    
    elif Config.MODE == 'cloud':
        print(f"Using cloud storage mode: {Config.CLOUD_API_URL}")
        return CloudStorage(
            api_url=Config.CLOUD_API_URL,
            api_key=Config.CLOUD_API_KEY,
            retry_attempts=Config.CLOUD_RETRY_ATTEMPTS,
            retry_delay=Config.CLOUD_RETRY_DELAY,
            enable_buffer=Config.CLOUD_ENABLE_BUFFER
        )
    
    else:
        raise ValueError(f"Invalid MODE: {Config.MODE}")


__all__ = ['get_storage', 'StorageBackend', 'LocalStorage', 'CloudStorage']

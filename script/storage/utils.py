"""Utility functions for storage CLI."""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console

from .adapters.base import StorageBackend
from .adapters.minio import MinioBackend
from .config import config_manager

console = Console()


def get_storage() -> Optional[StorageBackend]:
    """
    Factory function to get storage backend instance.
    
    Returns:
        StorageBackend instance or None if config not found
    """
    config = config_manager.get()
    if config is None:
        console.print("[red]Configuration not found. Run 'storage init' first.[/red]")
        return None
    
    return MinioBackend(
        endpoint_url=config.endpoint_url,
        access_key=config.access_key,
        secret_key=config.secret_key,
        bucket_name=config.bucket_name,
        secure=config.secure
    )


def generate_remote_path(filename: str, user_identifier: str, timestamp: Optional[datetime] = None) -> str:
    """
    Generate remote storage path following the pattern: embedded/{user}/{year}/{month}/{filename}
    
    Args:
        filename: Name of the file
        user_identifier: User identifier
        timestamp: Optional timestamp (defaults to now)
        
    Returns:
        Remote path string
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    year = timestamp.strftime('%Y')
    month = timestamp.strftime('%m')
    
    return f"embedded/{user_identifier}/{year}/{month}/{filename}"


def check_file_stability(filepath: str, check_interval: float = 1.0, max_checks: int = 5) -> bool:
    """
    Check if a file has finished being written by monitoring size stability.
    
    Args:
        filepath: Path to the file to check
        check_interval: Time (seconds) between checks
        max_checks: Maximum number of checks before assuming stable
        
    Returns:
        True if file is stable, False otherwise
    """
    if not os.path.exists(filepath):
        return False
    
    previous_size = -1
    checks = 0
    
    while checks < max_checks:
        try:
            current_size = os.path.getsize(filepath)
            
            if current_size == previous_size and current_size > 0:
                # File size hasn't changed, assume it's stable
                return True
            
            previous_size = current_size
            checks += 1
            
            if checks < max_checks:
                time.sleep(check_interval)
        except OSError:
            # File might have been moved or deleted
            return False
    
    # If we've done max checks and size keeps changing, assume it's still being written
    # Return True anyway to avoid infinite waiting
    return True


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def is_xml_file(filepath: str) -> bool:
    """
    Check if a file is an XML file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        True if file is XML, False otherwise
    """
    return Path(filepath).suffix.lower() == '.xml'

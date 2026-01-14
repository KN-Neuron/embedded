"""Abstract base class for storage backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class FileMetadata:
    """Metadata for a file in storage."""
    
    name: str
    size: int
    last_modified: datetime
    
    @property
    def user_identifier(self) -> str:
        """Extract user identifier from path (embedded/{user}/...)."""
        parts = self.name.split('/')
        if len(parts) >= 2 and parts[0] == 'embedded':
            return parts[1]
        return 'unknown'
    
    @property
    def year_month(self) -> str:
        """Extract year/month from path or last_modified."""
        parts = self.name.split('/')
        if len(parts) >= 4 and parts[0] == 'embedded':
            return f"{parts[2]}/{parts[3]}"
        return self.last_modified.strftime('%Y/%m')


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def upload(self, local_path: str, remote_path: str) -> bool:
        """
        Upload a file to remote storage.
        
        Args:
            local_path: Path to the local file
            remote_path: Destination path in remote storage
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def list_files(self, prefix: str = "") -> List[FileMetadata]:
        """
        List files in remote storage with optional prefix filter.
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of FileMetadata objects
        """
        pass
    
    @abstractmethod
    def download(self, remote_path: str, local_path: str) -> bool:
        """
        Download a file from remote storage.
        
        Args:
            remote_path: Path in remote storage
            local_path: Destination path for the downloaded file
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate the connection to the storage backend.
        
        Returns:
            True if connection is valid, False otherwise
        """
        pass

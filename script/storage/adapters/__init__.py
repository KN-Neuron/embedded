"""Storage adapters for different backends."""

from .base import StorageBackend, FileMetadata
from .minio import MinioBackend

__all__ = ["StorageBackend", "FileMetadata", "MinioBackend"]

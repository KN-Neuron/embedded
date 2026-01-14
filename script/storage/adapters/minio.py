"""Minio/S3-compatible storage backend implementation."""

import os
from pathlib import Path
from typing import List

from minio import Minio
from minio.error import S3Error

from .base import FileMetadata, StorageBackend


class MinioBackend(StorageBackend):
    """Storage backend using Minio client for S3-compatible storage (Cloudflare R2)."""
    
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = True
    ):
        """
        Initialize Minio backend.
        
        Args:
            endpoint_url: S3 endpoint (e.g., accountid.r2.cloudflarestorage.com)
            access_key: Access key ID
            secret_key: Secret access key
            bucket_name: Bucket name
            secure: Whether to use HTTPS (default: True)
        """
        self.bucket_name = bucket_name
        self.client = Minio(
            endpoint_url,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        """Upload a file to Minio storage."""
        try:
            # Ensure bucket exists
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
            
            # Upload file
            self.client.fput_object(
                self.bucket_name,
                remote_path,
                local_path
            )
            return True
        except S3Error as e:
            print(f"Error uploading file: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during upload: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[FileMetadata]:
        """List files in Minio storage with optional prefix."""
        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            
            files = []
            for obj in objects:
                files.append(FileMetadata(
                    name=obj.object_name,
                    size=obj.size,
                    last_modified=obj.last_modified
                ))
            
            return files
        except S3Error as e:
            print(f"Error listing files: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error during list: {e}")
            return []
    
    def download(self, remote_path: str, local_path: str) -> bool:
        """Download a file from Minio storage."""
        try:
            # Ensure local directory exists
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            self.client.fget_object(
                self.bucket_name,
                remote_path,
                local_path
            )
            return True
        except S3Error as e:
            print(f"Error downloading file: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during download: {e}")
            return False
    
    def validate_connection(self) -> bool:
        """Validate connection by checking if bucket is accessible."""
        try:
            # Try to check if bucket exists
            exists = self.client.bucket_exists(self.bucket_name)
            if not exists:
                # Try to create it
                self.client.make_bucket(self.bucket_name)
            return True
        except S3Error as e:
            print(f"Connection validation failed: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during connection validation: {e}")
            return False

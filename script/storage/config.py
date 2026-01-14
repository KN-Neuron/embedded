"""Configuration management for storage CLI."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class StorageConfig(BaseModel):
    """Configuration for storage sync."""
    
    bucket_name: str = Field(..., description="S3/R2 bucket name")
    endpoint_url: str = Field(..., description="S3 endpoint URL")
    access_key: str = Field(..., description="Access key ID")
    secret_key: str = Field(..., description="Secret access key")
    local_watch_folder: str = Field(..., description="Local folder to watch for new files")
    user_identifier: str = Field(..., description="User identifier for remote path organization")
    secure: bool = Field(default=True, description="Use HTTPS for connection")
    
    class Config:
        """Pydantic config."""
        validate_assignment = True


class ConfigManager:
    """Singleton configuration manager."""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[StorageConfig] = None
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def config_dir(self) -> Path:
        """Get configuration directory."""
        return Path.home() / '.storage'
    
    @property
    def config_path(self) -> Path:
        """Get configuration file path."""
        return self.config_dir / 'config.yaml'
    
    def load(self) -> Optional[StorageConfig]:
        """Load configuration from file."""
        if not self.config_path.exists():
            return None
        
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            self._config = StorageConfig(**data)
            return self._config
        except Exception as e:
            print(f"Error loading config: {e}")
            return None
    
    def save(self, config: StorageConfig) -> bool:
        """Save configuration to file."""
        try:
            # Ensure directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            with open(self.config_path, 'w') as f:
                yaml.safe_dump(config.model_dump(), f, default_flow_style=False)
            
            self._config = config
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self) -> Optional[StorageConfig]:
        """Get current configuration (load if not already loaded)."""
        if self._config is None:
            self._config = self.load()
        return self._config
    
    def exists(self) -> bool:
        """Check if configuration file exists."""
        return self.config_path.exists()


# Global config manager instance
config_manager = ConfigManager()

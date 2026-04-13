"""Application configuration"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration class"""

    # Server settings
    host: str = field(default="0.0.0.0")
    port: int = field(default=8080)
    debug: bool = field(default=False)

    # Authentication settings
    auth_token: str = field(default="")

    # Database settings
    database_url: str = field(default="")
    database_pool_size: int = field(default=10)
    database_max_overflow: int = field(default=20)
    database_pool_recycle: int = field(default=3600)

    # Data directory
    data_dir: str = field(default="./data")

    # Logging
    log_level: str = field(default="INFO")

    # API settings
    api_prefix: str = field(default="/api")

    # Object Storage settings
    cos_secret_id: str = field(default="")
    cos_secret_key: str = field(default="")
    cos_endpoint: str = field(default="")
    # Public base URL used to serve COS-hosted assets (e.g. skill icons)
    cos_base_url: str = field(default="")

    def __post_init__(self):
        """Validate configuration after initialization"""
        # Load environment variables from .env file
        # Use override=True to ensure .env file values override existing env vars
        load_dotenv(override=True)
        
        # Get environment variables (after loading .env)
        env_host = os.getenv("SKILL_HUB_HOST")
        env_port = os.getenv("SKILL_HUB_PORT")
        env_debug = os.getenv("SKILL_HUB_DEBUG")
        env_auth_token = os.getenv("SKILL_HUB_AUTH_TOKEN")
        env_database_url = os.getenv("SKILL_HUB_DATABASE_URL")
        env_database_pool_size = os.getenv("SKILL_HUB_DATABASE_POOL_SIZE")
        env_database_max_overflow = os.getenv("SKILL_HUB_DATABASE_MAX_OVERFLOW")
        env_database_pool_recycle = os.getenv("SKILL_HUB_DATABASE_POOL_RECYCLE")
        env_data_dir = os.getenv("SKILL_HUB_DATA_DIR")
        env_log_level = os.getenv("SKILL_HUB_LOG_LEVEL")
        env_api_prefix = os.getenv("SKILL_HUB_API_PREFIX")
        env_cos_secret_id = os.getenv("SKILL_HUB_COS_SECRET_ID")
        env_cos_secret_key = os.getenv("SKILL_HUB_COS_SECRET_KEY")
        env_cos_endpoint = os.getenv("SKILL_HUB_COS_ENDPOINT")
        env_cos_base_url = os.getenv("SKILL_HUB_COS_BASE_URL")
        
        # Apply environment variables only if not explicitly set in constructor
        # and environment variable exists
        if self.host == "0.0.0.0" and env_host:
            self.host = env_host
        
        if self.port == 8080 and env_port:
            try:
                self.port = int(env_port)
            except ValueError:
                pass  # Keep default if invalid
        
        if not self.debug and env_debug:
            self.debug = env_debug.lower() == "true"
        
        if not self.auth_token and env_auth_token:
            self.auth_token = env_auth_token
        
        if not self.database_url and env_database_url:
            self.database_url = env_database_url
        
        if self.database_pool_size == 10 and env_database_pool_size:
            try:
                self.database_pool_size = int(env_database_pool_size)
            except ValueError:
                pass  # Keep default if invalid
        
        if self.database_max_overflow == 20 and env_database_max_overflow:
            try:
                self.database_max_overflow = int(env_database_max_overflow)
            except ValueError:
                pass  # Keep default if invalid
        
        if self.database_pool_recycle == 3600 and env_database_pool_recycle:
            try:
                self.database_pool_recycle = int(env_database_pool_recycle)
            except ValueError:
                pass  # Keep default if invalid
        
        if self.data_dir == "./data" and env_data_dir:
            self.data_dir = env_data_dir
        
        if self.log_level == "INFO" and env_log_level:
            self.log_level = env_log_level
        
        if self.api_prefix == "/api" and env_api_prefix:
            self.api_prefix = env_api_prefix
            
        if not self.cos_secret_id and env_cos_secret_id:
            self.cos_secret_id = env_cos_secret_id
            
        if not self.cos_secret_key and env_cos_secret_key:
            self.cos_secret_key = env_cos_secret_key
            
        if not self.cos_endpoint and env_cos_endpoint:
            self.cos_endpoint = env_cos_endpoint

        if not self.cos_base_url and env_cos_base_url:
            self.cos_base_url = env_cos_base_url

        # Normalize cos_base_url by stripping any trailing slash to avoid
        # double-slashes when concatenating with object keys.
        if self.cos_base_url:
            self.cos_base_url = self.cos_base_url.rstrip("/")

        # Validate required fields
        if not self.auth_token:
            raise ValueError("SKILL_HUB_AUTH_TOKEN environment variable must be set")
        
        # Validate database URL if provided
        if self.database_url and not self.database_url.startswith(("postgresql://", "postgres://", "postgresql+asyncpg://")):
            raise ValueError("Database URL must start with postgresql:// or postgres:// or postgresql+asyncpg://")

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables"""
        return cls()
    
    @property
    def has_database(self) -> bool:
        """Check if database configuration is provided"""
        return bool(self.database_url)

"""Server class for managing the Flask application"""

import logging
import os
from typing import Optional
import asyncio
from hypercorn.config import Config as HypercornConfig
from hypercorn.asyncio import serve
from quart import Quart

from skill_hub.config.config import Config
from skill_hub.server.app import create_app
from skill_hub.db.database import init_db, close_db

logger = logging.getLogger(__name__)


class Server:
    """Server class for managing the Quart application lifecycle"""
    
    def __init__(self, config: Config):
        """Initialize the server
        
        Args:
            config: Application configuration
        """
        self._config = config
        self._app = None
    
    @property
    def config(self) -> Config:
        """Get the server configuration"""
        return self._config
    
    @property
    def app(self) -> Optional[Quart]:
        """Get the Quart application instance"""
        return self._app
    
    def start(self):
        """Start the server"""
        logger.info("Starting Skill Hub server")
        
        try:
            # Create data directory if it doesn't exist
            self._setup_data_dir()
            
            # Initialize database
            self._init_database()
            
            # Create Quart application
            self._app = create_app(self._config)
            
            # Start the server
            logger.info(f"Server starting on {self._config.host}:{self._config.port}")
            logger.info(f"API prefix: {self._config.api_prefix}")
            logger.info(f"Debug mode: {self._config.debug}")
            
            if self._config.has_database:
                logger.info(f"Database: {self._config.database_url.split('@')[-1] if '@' in self._config.database_url else self._config.database_url}")
            else:
                logger.info("Database: Not configured")
            
            # Configure hypercorn
            hc_config = HypercornConfig()
            hc_config.bind = [f"{self._config.host}:{self._config.port}"]
            hc_config.use_reloader = self._config.debug
            
            # Run the Quart app with Hypercorn
            asyncio.run(serve(self._app, hc_config))
            
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            self._cleanup()
    
    def _setup_data_dir(self):
        """Create data directory if it doesn't exist"""
        data_dir = self._config.data_dir
        
        if not os.path.exists(data_dir):
            logger.info(f"Creating data directory: {data_dir}")
            os.makedirs(data_dir, exist_ok=True)
        
        # Create subdirectories if needed
        subdirs = ["logs", "uploads", "cache"]
        for subdir in subdirs:
            subdir_path = os.path.join(data_dir, subdir)
            if not os.path.exists(subdir_path):
                os.makedirs(subdir_path, exist_ok=True)
    
    def _init_database(self):
        """Initialize database connections"""
        try:
            init_db(self._config)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            if self._config.has_database:
                # If database is configured but fails to initialize, we might want to fail fast
                raise
    
    def _cleanup(self):
        """Cleanup resources before shutdown"""
        logger.info("Cleaning up resources...")
        
        # Close database connections
        try:
            close_db()
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
        
        logger.info("Cleanup completed")

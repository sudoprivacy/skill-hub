"""Flask application factory"""

import logging
from quart import Quart
from skill_hub.config.config import Config
from quart_schema import QuartSchema, Info
from skill_hub.api.exceptions import register_error_handlers
from skill_hub.api.auth import AuthMiddleware
from skill_hub.routes.routes import register_routes


def create_app(config: Config) -> Quart:
    """Create and configure the Quart application
    
    Args:
        config: Application configuration
        
    Returns:
        Configured Quart application
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Create Quart app
    app = Quart(__name__)
    
    # Configure OpenAPI / Redoc
    QuartSchema(
        app,
        info=Info(title="Skill Hub API", version="0.1.0", description="API for Skill Hub"),
        openapi_path=f"{config.api_prefix}/openapi.json",
        swagger_ui_path=f"{config.api_prefix}/docs",
        redoc_ui_path=f"{config.api_prefix}/redoc",
    )
    
    # Store configuration in app
    app.config["APP_CONFIG"] = config
    
    # Configure app settings
    app.config["DEBUG"] = config.debug
    app.config["SECRET_KEY"] = config.auth_token  # Use auth token as secret key
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB limit

    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize authentication middleware
    auth_middleware = AuthMiddleware(
        app=app,
        protected_prefixes=[config.api_prefix]
    )
    
    # Register routes
    register_routes(app, config)
    
    # Add health check endpoint
    @app.route("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": "skill-hub"}
    
    # Add root endpoint
    @app.route("/")
    async def root():
        """Root endpoint"""
        return {
            "service": "skill-hub",
            "version": "0.1.0",
            "docs": f"{config.api_prefix}/docs",
            "health": "/health",
        }
    
    return app

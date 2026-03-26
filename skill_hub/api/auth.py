"""Authentication module - Fixed header token authentication"""

import logging
from functools import wraps
from typing import Callable

from quart import request, current_app, g

from skill_hub.api.exceptions import UnauthorizedException

logger = logging.getLogger(__name__)

# Header name for authentication token
AUTH_HEADER_NAME = "Authorization"
TOKEN_PREFIX = "Bearer "


def get_token_from_header() -> str | None:
    """Extract token from Authorization header
    
    Supports format: "Bearer <token>" or just "<token>"
    
    Returns:
        Token string if found, None otherwise
    """
    auth_header = request.headers.get(AUTH_HEADER_NAME)
    if not auth_header:
        return None
    
    # Support both "Bearer <token>" and raw token format
    if auth_header.startswith(TOKEN_PREFIX):
        return auth_header[len(TOKEN_PREFIX):]
    
    return auth_header


def verify_token(token: str) -> bool:
    """Verify if the provided token matches the configured auth token
    
    Args:
        token: Token to verify
        
    Returns:
        True if token is valid, False otherwise
    """
    config = current_app.config.get("APP_CONFIG")
    if not config:
        logger.error("Application configuration not found")
        return False
    
    return token == config.auth_token


def token_required(f: Callable) -> Callable:
    """Decorator to require valid token authentication
    
    Usage:
        @app.route('/protected')
        @token_required
        async def protected_route():
            return {"message": "This is protected"}
    """
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            logger.warning("Missing authentication token")
            raise UnauthorizedException(message="Missing authentication token")
        
        if not verify_token(token):
            logger.warning("Invalid authentication token")
            raise UnauthorizedException(message="Invalid authentication token")
        
        # Store authentication status in g for later use
        g.authenticated = True
        
        return await f(*args, **kwargs)
    
    return decorated_function


class AuthMiddleware:
    """Middleware class for handling authentication on specific routes"""
    
    def __init__(self, app=None, protected_prefixes: list[str] = None):
        """Initialize the middleware
        
        Args:
            app: Quart application instance
            protected_prefixes: List of URL prefixes that require authentication
        """
        self.app = app
        self.protected_prefixes = protected_prefixes or ["/api/v1"]
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with a Quart application
        
        Args:
            app: Quart application instance
        """
        self.app = app
        app.before_request(self._check_auth)
    
    async def _check_auth(self):
        """Check authentication before each request"""
        # Skip authentication for non-protected routes
        path = request.path
        
        # Allow openapi docs paths even if they are under protected prefix
        if path.endswith("/docs") or path.endswith("/openapi.json") or path.endswith("/redoc"):
            return None
        
        # Check if the path starts with any protected prefix
        requires_auth = any(path.startswith(prefix) for prefix in self.protected_prefixes)
        
        if not requires_auth:
            return None
        
        token = get_token_from_header()
        
        if not token:
            raise UnauthorizedException(message="Missing authentication token")
        
        if not verify_token(token):
            raise UnauthorizedException(message="Invalid authentication token")
        
        g.authenticated = True
        return None

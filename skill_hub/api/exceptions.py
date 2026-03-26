r"""API Exceptions module"""

import logging
from typing import Optional, Dict, Any

from quart import Quart, jsonify

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Base API exception class"""
    
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    
    def __init__(
        self,
        message: str = "An error occurred",
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        response = {
            "error": {
                "code": self.error_code,
                "message": self.message,
            }
        }
        if self.details:
            response["error"]["details"] = self.details
        return response


class BadRequestException(APIException):
    """400 Bad Request exception"""
    
    status_code = 400
    error_code = "BAD_REQUEST"
    
    def __init__(self, message: str = "Bad request", **kwargs):
        super().__init__(message=message, **kwargs)


class UnauthorizedException(APIException):
    """401 Unauthorized exception"""
    
    status_code = 401
    error_code = "UNAUTHORIZED"
    
    def __init__(self, message: str = "Unauthorized", **kwargs):
        super().__init__(message=message, **kwargs)


class ForbiddenException(APIException):
    """403 Forbidden exception"""
    
    status_code = 403
    error_code = "FORBIDDEN"
    
    def __init__(self, message: str = "Forbidden", **kwargs):
        super().__init__(message=message, **kwargs)


class NotFoundException(APIException):
    """404 Not Found exception"""
    
    status_code = 404
    error_code = "NOT_FOUND"
    
    def __init__(self, message: str = "Resource not found", **kwargs):
        super().__init__(message=message, **kwargs)


class ConflictException(APIException):
    """409 Conflict exception"""
    
    status_code = 409
    error_code = "CONFLICT"
    
    def __init__(self, message: str = "Resource conflict", **kwargs):
        super().__init__(message=message, **kwargs)


class InternalServerErrorException(APIException):
    """500 Internal Server Error exception"""
    
    status_code = 500
    error_code = "INTERNAL_SERVER_ERROR"
    
    def __init__(self, message: str = "Internal server error", **kwargs):
        super().__init__(message=message, **kwargs)


def register_error_handlers(app: Quart) -> None:
    """Register error handlers for the Quart application
    
    Args:
        app: Quart application instance
    """
    
    @app.errorhandler(APIException)
    async def handle_api_exception(error: APIException):
        """Handle custom API exceptions"""
        logger.error(f"API Exception: {error.error_code} - {error.message}")
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(400)
    async def handle_bad_request(error):
        """Handle 400 Bad Request errors"""
        response = jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": str(error.description) if hasattr(error, 'description') else "Bad request",
            }
        })
        response.status_code = 400
        return response
    
    @app.errorhandler(404)
    async def handle_not_found(error):
        """Handle 404 Not Found errors"""
        response = jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found",
            }
        })
        response.status_code = 404
        return response
    
    @app.errorhandler(405)
    async def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed errors"""
        response = jsonify({
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "The method is not allowed for the requested URL",
            }
        })
        response.status_code = 405
        return response
    
    @app.errorhandler(500)
    async def handle_internal_error(error):
        """Handle 500 Internal Server errors"""
        logger.error(f"Internal Server Error: {error}")
        response = jsonify({
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
            }
        })
        response.status_code = 500
        return response

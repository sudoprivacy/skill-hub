"""Authentication routes"""

from quart import Blueprint, request, current_app
from skill_hub.api.responses import success_response, error_response
from skill_hub.api.auth import get_token_from_header, verify_token

auth_router = Blueprint("auth", __name__)

@auth_router.route("/verify", methods=["GET"])
async def verify():
    """Verify authentication token from header
    
    This endpoint verifies the token from the Authorization header.
    
    Headers:
        Authorization: Bearer <token> or <token>
    
    Returns:
        Success response with verification status
    """
    try:
        token = get_token_from_header()
        
        if not token:
            return error_response(
                message="Authorization header is required",
                status_code=401,
                error_code="UNAUTHORIZED"
            )
        
        if verify_token(token):
            return success_response(
                data={
                    "authenticated": True,
                    "message": "Token is valid"
                },
                message="Verification successful"
            )
        else:
            return error_response(
                message="Invalid token",
                status_code=401,
                error_code="UNAUTHORIZED"
            )
    
    except Exception as e:
        return error_response(
            message=f"Verification failed: {str(e)}",
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR"
        )


@auth_router.route("/info", methods=["GET"])
async def auth_info():
    """Get authentication information
    
    Returns information about the authentication configuration.
    
    Returns:
        Authentication configuration information
    """
    config = current_app.config.get("APP_CONFIG")
    
    if not config:
        return error_response(
            message="Configuration not found",
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR"
        )
    
    return success_response(
        data={
            "auth_type": "fixed_token",
            "header_name": "Authorization",
            "token_prefix": "Bearer",
            "api_prefix": config.api_prefix,
        },
        message="Authentication information"
    )

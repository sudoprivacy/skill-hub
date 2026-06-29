"""Authentication routes"""

from quart import Blueprint, request, current_app
from skill_hub.api.responses import success_response, error_response
from skill_hub.api.auth import (
    get_token_from_header,
    verify_token,
    issue_user_token,
    get_current_user,
)
from skill_hub.api.exceptions import BadRequestException, UnauthorizedException
from skill_hub.db.database import get_session
from skill_hub.services.user_service import UserService

auth_router = Blueprint("auth", __name__)


@auth_router.route("/login", methods=["POST"])
async def login():
    """Username + password login. Returns a signed token and user info."""
    data = await request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        raise BadRequestException(message="用户名和密码不能为空")

    async with get_session() as session:
        user_service = UserService(session)
        user = await user_service.authenticate(username, password)
        if not user:
            raise UnauthorizedException(message="用户名或密码错误")
        role_name = user.role.name if user.role else "user"
        token = issue_user_token(user.id, user.username, role_name)
        payload = {
            "token": token,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "display_name": user.display_name,
                "role": role_name,
            },
        }

    return success_response(data=payload, message="登录成功")


@auth_router.route("/me", methods=["GET"])
async def me():
    """Return the current authenticated identity."""
    user = get_current_user()
    if not user:
        raise UnauthorizedException(message="未登录")
    return success_response(data=user, message="OK")

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

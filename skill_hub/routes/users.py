"""User management routes (admin only)."""

from quart import Blueprint, request

from skill_hub.api.auth import token_required, require_admin, ROLE_ADMIN, ROLE_USER
from skill_hub.api.responses import success_response
from skill_hub.api.exceptions import BadRequestException, NotFoundException
from skill_hub.db.database import get_session
from skill_hub.services.user_service import UserService

users_router = Blueprint("users", __name__)

_VALID_ROLES = {ROLE_ADMIN, ROLE_USER}


@users_router.route("", methods=["GET"])
@token_required
async def list_users():
    """List all users (admin only)."""
    require_admin()
    async with get_session() as session:
        service = UserService(session)
        users = await service.list_users()
        data = [u.to_dict() for u in users]
    return success_response(data=data, message="Users retrieved successfully")


@users_router.route("", methods=["POST"])
@token_required
async def create_user():
    """Create a user with a role (admin only)."""
    require_admin()
    data = await request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = data.get("role") or ROLE_USER
    display_name = data.get("display_name")

    if not username or not password:
        raise BadRequestException(message="用户名和密码不能为空")
    if role not in _VALID_ROLES:
        raise BadRequestException(message="角色只能是 admin 或 user")

    async with get_session() as session:
        service = UserService(session)
        if await service.get_by_username(username):
            raise BadRequestException(message="用户名已存在")
        user = await service.create(
            username=username,
            password=password,
            role_name=role,
            display_name=display_name,
        )
        result = user.to_dict()
    return success_response(data=result, message="用户创建成功", status_code=201)


@users_router.route("/<user_id>", methods=["PUT"])
@token_required
async def update_user(user_id: str):
    """Update a user: role / password reset / active / display name (admin)."""
    require_admin()
    data = await request.get_json(silent=True) or {}

    role = data.get("role")
    if role is not None and role not in _VALID_ROLES:
        raise BadRequestException(message="角色只能是 admin 或 user")

    async with get_session() as session:
        service = UserService(session)
        user = await service.update(
            user_id,
            password=data.get("password") or None,
            role_name=role,
            display_name=data.get("display_name"),
            is_active=data.get("is_active"),
        )
        if not user:
            raise NotFoundException(message="用户不存在")
        result = user.to_dict()
    return success_response(data=result, message="用户更新成功")


@users_router.route("/<user_id>", methods=["DELETE"])
@token_required
async def delete_user(user_id: str):
    """Delete a user (admin only)."""
    require_admin()
    async with get_session() as session:
        service = UserService(session)
        deleted = await service.delete(user_id)
        if not deleted:
            raise NotFoundException(message="用户不存在")
    return success_response(message="用户删除成功")

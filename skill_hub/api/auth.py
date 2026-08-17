"""Authentication & authorization.

Two credential types are accepted on the same Bearer header:

1. **User token** — a signed (itsdangerous) token issued at login, carrying
   ``{uid, username, role}``. This is how human admins/users authenticate.
2. **Fixed token** — the legacy ``AUTH_TOKEN``. Treated as a full-power
   "system" account (role=admin, id=None), so the crawler/spider keeps
   ingesting data unchanged.

The resolved identity is stored on ``g.current_user`` for downstream
permission checks (``require_admin`` / ``require_owner_or_admin``).
"""

import logging
from functools import wraps
from typing import Callable, Optional

from quart import request, current_app, g
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from skill_hub.api.exceptions import UnauthorizedException, ForbiddenException

logger = logging.getLogger(__name__)

AUTH_HEADER_NAME = "Authorization"
TOKEN_PREFIX = "Bearer "

ROLE_ADMIN = "admin"
ROLE_USER = "user"

# Signed-token settings
_TOKEN_SALT = "skill-hub-auth"
TOKEN_MAX_AGE = 7 * 24 * 3600  # 7 days

# Synthetic identity for the fixed (system) token
SYSTEM_USER = {"id": None, "username": "system", "role": ROLE_ADMIN}


def get_token_from_header() -> Optional[str]:
    """Extract token from the Authorization header (Bearer or raw)."""
    auth_header = request.headers.get(AUTH_HEADER_NAME)
    if not auth_header:
        return None
    if auth_header.startswith(TOKEN_PREFIX):
        return auth_header[len(TOKEN_PREFIX):]
    return auth_header


def verify_token(token: str) -> bool:
    """Return True if token equals the configured fixed (system) token."""
    config = current_app.config.get("APP_CONFIG")
    if not config:
        logger.error("Application configuration not found")
        return False
    return bool(config.auth_token) and token == config.auth_token


# --------------------------------------------------------------------------
# Signed user tokens (login)
# --------------------------------------------------------------------------

def _serializer() -> URLSafeTimedSerializer:
    config = current_app.config.get("APP_CONFIG")
    secret = config.auth_token if config else "insecure-dev-secret"
    return URLSafeTimedSerializer(secret, salt=_TOKEN_SALT)


def issue_user_token(user_id, username: str, role: str) -> str:
    """Issue a signed token for a logged-in user."""
    return _serializer().dumps(
        {"uid": str(user_id), "username": username, "role": role}
    )


def decode_user_token(token: str) -> Optional[dict]:
    """Verify and decode a user token; None if invalid/expired."""
    try:
        return _serializer().loads(token, max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def _resolve_current_user(token: str) -> Optional[dict]:
    """Resolve a Bearer token to an identity dict, or None if invalid."""
    data = decode_user_token(token)
    if data:
        return {
            "id": data.get("uid"),
            "username": data.get("username"),
            "role": data.get("role"),
        }
    if verify_token(token):
        return dict(SYSTEM_USER)
    return None


# --------------------------------------------------------------------------
# Identity & permission helpers
# --------------------------------------------------------------------------

def get_current_user() -> Optional[dict]:
    """Return the identity resolved for this request (or None)."""
    return getattr(g, "current_user", None)


def is_admin() -> bool:
    user = get_current_user()
    return bool(user and user.get("role") == ROLE_ADMIN)


def require_admin() -> None:
    """Raise 403 unless the current user is an admin."""
    if not is_admin():
        raise ForbiddenException(message="需要管理员权限")


def require_owner_or_admin(creator_id) -> None:
    """Raise 403 unless current user is admin or the resource's creator."""
    if is_admin():
        return
    user = get_current_user()
    if user and creator_id and str(creator_id) == str(user.get("id")):
        return
    raise ForbiddenException(message="只能操作自己创建的内容")


# --------------------------------------------------------------------------
# Enforcement: decorator + middleware
# --------------------------------------------------------------------------

def token_required(f: Callable) -> Callable:
    """Decorator requiring a valid user token or the fixed system token."""

    @wraps(f)
    async def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            raise UnauthorizedException(message="Missing authentication token")

        user = _resolve_current_user(token)
        if not user:
            raise UnauthorizedException(message="Invalid authentication token")

        g.current_user = user
        g.authenticated = True
        return await f(*args, **kwargs)

    return decorated_function


class AuthMiddleware:
    """before_request hook enforcing auth on protected prefixes."""

    def __init__(self, app=None, protected_prefixes: list[str] = None):
        self.app = app
        self.protected_prefixes = protected_prefixes or ["/api/v1"]
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.before_request(self._check_auth)

    async def _check_auth(self):
        path = request.path

        # Allow OpenAPI docs even under a protected prefix
        if path.endswith("/docs") or path.endswith("/openapi.json") or path.endswith("/redoc"):
            return None

        requires_auth = any(
            path.startswith(prefix) for prefix in self.protected_prefixes
        )
        if not requires_auth:
            return None

        # Login is the one protected-prefix endpoint that must be public.
        if path.endswith("/auth/login"):
            return None

        token = get_token_from_header()
        if not token:
            raise UnauthorizedException(message="Missing authentication token")

        user = _resolve_current_user(token)
        if not user:
            raise UnauthorizedException(message="Invalid authentication token")

        g.current_user = user
        g.authenticated = True
        return None

"""Routes module"""

from skill_hub.routes.routes import register_routes
from skill_hub.routes.health import health_router
from skill_hub.routes.auth import auth_router
from skill_hub.routes.skills import skills_router

__all__ = [
    "register_routes",
    "health_router",
    "auth_router",
    "skills_router",
]

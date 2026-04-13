"""Route registration module"""

from quart import Quart

from skill_hub.config.config import Config
from skill_hub.routes.health import health_router
from skill_hub.routes.auth import auth_router
from skill_hub.routes.skills import skills_router
from skill_hub.routes.skill_versions import skill_versions_router
from skill_hub.routes.categories import categories_router
from skill_hub.routes.assistants import assistants_router

def register_routes(app: Quart, config: Config) -> None:
    """Register all routes with the Quart application

    Args:
        app: Quart application instance
        config: Application configuration
    """
    # Register health routes
    app.register_blueprint(health_router)

    # Register auth routes
    app.register_blueprint(auth_router, url_prefix=f"{config.api_prefix}/auth")

    # Register skills routes
    app.register_blueprint(skills_router, url_prefix=f"{config.api_prefix}/skills")

    # Register skill versions routes
    app.register_blueprint(skill_versions_router, url_prefix=f"{config.api_prefix}/skill-versions")

    # Register categories routes
    app.register_blueprint(categories_router, url_prefix=f"{config.api_prefix}/categories")

    # Register assistants routes
    app.register_blueprint(assistants_router, url_prefix=f"{config.api_prefix}/assistants")
    
    # The /docs endpoint is now handled by quart-schema for Swagger UI
    # We can provide a custom api-list if needed, but usually the OpenAPI specs are sufficient.
    # @app.route(f"{config.api_prefix}/endpoints")
    # async def api_docs():
    #     """API endpoints listing"""
    #     return {
    #         "endpoints": {
    #             "auth": {
    #                 "login": f"{config.api_prefix}/auth/login",
    #                 "verify": f"{config.api_prefix}/auth/verify",
    #             },
    #             "skills": {
    #                 "list_skills [GET]": f"{config.api_prefix}/skills",
    #                 "get_skill [GET]": f"{config.api_prefix}/skills/<skill_id>",
    #                 "add_skill [POST]": f"{config.api_prefix}/skills/add",
    #             },
    #             "health": "/health",
    #         }
    #     }

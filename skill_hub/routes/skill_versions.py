"""Skill Versions management routes"""

from quart import Blueprint, request, g
from skill_hub.api.responses import (
    success_response,
    error_response,
    paginated_response,
)
from skill_hub.api.auth import token_required
from skill_hub.db.database import get_session
from skill_hub.services.skill_version_service import SkillVersionService

skill_versions_router = Blueprint("skill_versions", __name__)


@skill_versions_router.route("/<version_id>", methods=["GET"])
@token_required
async def get_skill_version(version_id):
    """Get a specific skill version by ID
    
    Args:
        version_id: Skill version ID (UUID)
    
    Returns:
        Skill version details
    """
    try:
        async with get_session() as session:
            skill_version_service = SkillVersionService(session)
            skill_version = await skill_version_service.get_by_id(version_id)
            
            if not skill_version:
                return error_response(
                    message=f"Skill version with ID {version_id} not found",
                    status_code=404,
                    error_code="NOT_FOUND",
                )
            
            return success_response(
                data=skill_version.to_dict(),
                message="Skill version retrieved successfully",
            )
    
    except Exception as e:
        return error_response(
            message=f"Failed to get skill version: {str(e)}",
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR",
        )

"""Skill Versions management routes"""

from quart import Blueprint, request, g, current_app
import os
import uuid
import logging
from skill_hub.api.responses import (
    success_response,
    error_response,
    paginated_response,
)
from skill_hub.api.auth import token_required
from skill_hub.db.database import get_session
from skill_hub.services.skill_version_service import SkillVersionService
from skill_hub.services.skill_service import SkillService
from skill_hub.utils.object_storage_client import ObjectStorageClient
from skill_hub.api.exceptions import BadRequestException

skill_versions_router = Blueprint("skill_versions", __name__)
logger = logging.getLogger(__name__)


@skill_versions_router.route("/", methods=["POST"])
@token_required
async def create_skill_version():
    """Create a new skill version from uploaded zip file"""
    try:
        form_data = await request.form
        skill_id = form_data.get("skill_id")
        version = form_data.get("version")
        # changelog = form_data.get("changelog", "")

        if not skill_id or not version:
            raise BadRequestException(message="skill_id and version are required")

        files = await request.files
        skill_file = files.get("skill_file")

        if not skill_file:
            raise BadRequestException(message="skill_file (zip package) is required")

        if not skill_file.filename.endswith('.zip'):
            raise BadRequestException(message="skill_file must be a .zip file")

        # Config setup
        config = current_app.config.get("APP_CONFIG")
        upload_dir = getattr(config, "upload_dir", "data/uploads")

        # Temp dir logic matching skill creation
        temp_id = str(uuid.uuid4())
        temp_dir = os.path.join(upload_dir, "temp", temp_id)
        os.makedirs(temp_dir, exist_ok=True)
        skill_file_path = os.path.join(temp_dir, skill_file.filename)

        skill_object_key = ""

        try:
            # 1. Save zip to disk temporarily
            await skill_file.save(skill_file_path)

            # 3. Verify skill exists
            async with get_session() as session:
                skill_service = SkillService(session)
                skill = await skill_service.get_by_id(skill_id)
                if not skill:
                    raise BadRequestException(message=f"Skill with ID {skill_id} not found")

            # 4. Upload zip to COS
            cos_client = ObjectStorageClient(config)
            bucket_name = "sudoclaw-1309794936"

            # Use original skill_id for path matching existing pattern
            skill_object_key = f"skill-hub/{skill_id}/{version}/{skill_file.filename}"

            if cos_client.client:
                success = cos_client.upload_file(
                    bucket_name=bucket_name,
                    local_file_path=skill_file_path,
                    object_key=skill_object_key
                )
                if not success:
                    raise Exception("Failed to upload skill package to object storage")
            else:
                logger.warning("ObjectStorageClient not initialized, skipping COS upload")
                # Fallback for local testing if COS not configured
                skill_object_key = f"/uploads/skills/{skill_id}/{version}/{skill_file.filename}"

        finally:
            # Cleanup temp files
            try:
                if os.path.exists(skill_file_path):
                    os.remove(skill_file_path)

                # Cleanup extracted directory if it exists
                extracted_dir = os.path.join(temp_dir, skill_file.filename.replace('.zip', ''))
                if os.path.exists(extracted_dir):
                    for root, dirs, files in os.walk(extracted_dir, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(extracted_dir)

                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp files: {str(e)}")

        # Create record in DB
        async with get_session() as session:
            skill_version_service = SkillVersionService(session)

            version_data = {
                "skill_id": skill_id,
                "version": version,
                "source_url": skill_object_key,
                "checksum": "",
                "changelog": "",
                "readme_content": ""
            }

            db_version = await skill_version_service.create(version_data)

            return success_response(
                data=db_version.to_dict(),
                message="Skill version created successfully",
                status_code=201
            )

    except BadRequestException as e:
        return error_response(
            message=str(e.message),
            status_code=e.status_code,
            error_code=e.error_code
        )
    except Exception as e:
        logger.error(f"Error creating skill version: {str(e)}", exc_info=True)
        return error_response(
            message=f"Failed to create skill version: {str(e)}",
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR",
        )

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

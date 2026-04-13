"""Assistants management routes"""

import os
import uuid
import logging
from quart import Blueprint, request, current_app

from skill_hub.api.auth import token_required
from skill_hub.schemas.assistant_schemas import AssistantCreateRequest, AssistantUpdateRequest
from skill_hub.services.assistant_service import AssistantService
from skill_hub.db.database import get_session
from skill_hub.api.responses import success_response
from skill_hub.api.exceptions import BadRequestException, NotFoundException
from skill_hub.utils.object_storage_client import ObjectStorageClient

logger = logging.getLogger(__name__)

assistants_router = Blueprint("assistants", __name__)


@assistants_router.route("/cursor", methods=["GET"])
@token_required
async def list_assistants_cursor():
    """
    # 获取数字助手列表 (游标分页)

    获取支持游标分页和过滤的数字助手列表。

    ## 查询参数 (Query Parameters)

    * `cursor` (str, 可选): 下一页结果的游标。
    * `limit` (int, 可选): 每次请求返回的记录数。默认为 `10`。
    * `query` (str, 可选): 用于匹配助手名称或描述的搜索关键字。
    * `category_id` (str, 可选): 用于过滤助手列表的分类 ID。
    """
    cursor = request.args.get("cursor", None)
    limit = request.args.get("limit", 10, type=int)
    query = request.args.get("query", "")
    category_id = request.args.get("category_id", "")

    async with get_session() as session:
        assistant_service = AssistantService(session)
        result = await assistant_service.list_all_cursor(
            cursor=cursor,
            limit=limit,
            search=query if query else None,
            category_id=category_id if category_id else None
        )

        assistants_data = [a.to_dict() for a in result["assistants"]]
        result["assistants"] = assistants_data

    return success_response(
        data=result,
        message="Assistants retrieved successfully"
    )

@assistants_router.route("/<assistant_id>", methods=["GET"])
@token_required
async def get_assistant(assistant_id: str):
    """Get assistant by ID"""
    async with get_session() as session:
        assistant_service = AssistantService(session)
        assistant = await assistant_service.get_by_id(assistant_id)
        if not assistant:
            raise NotFoundException(message="Assistant not found")

        # Format the assistant to prepend CDN URL
        formatted_assistant = assistant_service._format_assistants([assistant])[0]

    return success_response(
        data=formatted_assistant.to_dict(),
        message="Assistant retrieved successfully"
    )

@assistants_router.route("", methods=["POST"])
@token_required
async def create_assistant():
    """Create a new assistant"""
    form_data = await request.form
    files = await request.files

    if not form_data and not files:
        raise BadRequestException(message="Invalid payload")

    req = AssistantCreateRequest.from_dict(form_data)
    is_valid, error = req.validate()
    if not is_valid:
        raise BadRequestException(message=error)

    # Get files
    prompt_file = files.get("prompt_file")
    avatar_file = files.get("avatar")

    # Validate files
    if prompt_file and not prompt_file.filename.endswith('.md'):
        raise BadRequestException(message="promptFile must be a .md file")

    if avatar_file and not avatar_file.filename.endswith('.png'):
        raise BadRequestException(message="avatar must be a .png file")

    # Pre-generate UUID for both storage and database
    assistant_id = str(uuid.uuid4())

    async with get_session() as session:
        assistant_service = AssistantService(session)

        # Check if name already exists
        existing = await assistant_service.get_by_name(req.name)
        if existing:
            raise BadRequestException(message="Assistant name already exists")

        # Check if we need to upload files
        has_files = prompt_file or avatar_file

        if has_files:
            config = current_app.config.get("APP_CONFIG")
            upload_dir = getattr(config, "upload_dir", "data/uploads")

            # Save files temporarily
            temp_dir = os.path.join(upload_dir, "temp", "assistants", assistant_id)
            os.makedirs(temp_dir, exist_ok=True)

            prompt_file_path = None
            prompt_object_key = None
            if prompt_file:
                prompt_file_path = os.path.join(temp_dir, prompt_file.filename)
                await prompt_file.save(prompt_file_path)
                prompt_object_key = f"assistant-hub/{assistant_id}/{prompt_file.filename}"

            avatar_file_path = None
            avatar_object_key = None
            if avatar_file:
                avatar_file_path = os.path.join(temp_dir, "avatar.png")
                await avatar_file.save(avatar_file_path)
                avatar_object_key = f"assistant-hub/{assistant_id}/avatar.png"

            # Upload to Tencent Cloud Object Storage
            try:
                cos_client = ObjectStorageClient(config)

                if cos_client.client:
                    bucket_name = "sudoclaw-1309794936" # Following skills.py convention

                    if prompt_file_path and prompt_object_key:
                        cos_client.upload_file(
                            bucket_name=bucket_name,
                            local_file_path=prompt_file_path,
                            object_key=prompt_object_key
                        )
                        req.prompt_file = prompt_object_key

                    if avatar_file_path and avatar_object_key:
                        cos_client.upload_file(
                            bucket_name=bucket_name,
                            local_file_path=avatar_file_path,
                            object_key=avatar_object_key
                        )
                        req.avatar = avatar_object_key
                else:
                    logger.warning("ObjectStorageClient is not initialized")
            except Exception as e:
                logger.error(f"Error uploading to object storage: {str(e)}")
                raise BadRequestException(message=f"Failed to upload files: {str(e)}")

            # Cleanup temp files
            try:
                if prompt_file_path and os.path.exists(prompt_file_path):
                    os.remove(prompt_file_path)
                if avatar_file_path and os.path.exists(avatar_file_path):
                    os.remove(avatar_file_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp files: {str(e)}")

        assistant_data = req.to_assistant_data()
        assistant_data["id"] = assistant_id

        assistant = await assistant_service.create(assistant_data)
        assistant_dict = assistant.to_dict()

    return success_response(
        data=assistant_dict,
        message="Assistant created successfully",
        status_code=201
    )

@assistants_router.route("/<assistant_id>", methods=["PUT"])
@token_required
async def update_assistant(assistant_id: str):
    """Update an existing assistant"""
    data = await request.get_json()
    if not data:
        raise BadRequestException(message="Invalid JSON payload")
        
    req = AssistantUpdateRequest.from_dict(data)
    is_valid, error = req.validate()
    if not is_valid:
        raise BadRequestException(message=error)
        
    async with get_session() as session:
        assistant_service = AssistantService(session)
        
        # Ensure we aren't updating to an existing name
        if req.name is not None:
            existing = await assistant_service.get_by_name(req.name)
            # If name exists and it's a DIFFERENT assistant
            if existing and str(existing.id) != assistant_id:
                raise BadRequestException(message="Assistant name already exists")
                
        assistant = await assistant_service.update(assistant_id, req.to_update_data())
        if not assistant:
            raise NotFoundException(message="Assistant not found")
            
        assistant_dict = assistant.to_dict()
        
    return success_response(
        data=assistant_dict,
        message="Assistant updated successfully"
    )

@assistants_router.route("/<assistant_id>", methods=["DELETE"])
@token_required
async def delete_assistant(assistant_id: str):
    """Delete an assistant"""
    async with get_session() as session:
        assistant_service = AssistantService(session)
        deleted = await assistant_service.delete(assistant_id)
        if not deleted:
            raise NotFoundException(message="Assistant not found")
            
    return success_response(
        message="Assistant deleted successfully"
    )

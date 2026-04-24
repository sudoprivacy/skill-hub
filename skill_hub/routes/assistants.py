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
    * `category` (str, 可选): 用于过滤助手列表的分类名称，匹配 categories 数组。
    * `tenant_id` (str, 可选): 租户ID，用于过滤特定租户的助手。如果不传则只返回公共(无租户)的助手。
    """
    cursor = request.args.get("cursor", None)
    limit = request.args.get("limit", 10, type=int)
    query = request.args.get("query", "")
    category = request.args.get("category", "")
    tenant_id = request.args.get("tenant_id", None)

    async with get_session() as session:
        assistant_service = AssistantService(session)
        result = await assistant_service.list_all_cursor(
            cursor=cursor,
            limit=limit,
            search=query if query else None,
            category=category if category else None,
            tenant_id=tenant_id
        )

        assistants_data = [a.to_dict() for a in result["assistants"]]
        result["assistants"] = assistants_data

    return success_response(
        data=result,
        message="Assistants retrieved successfully"
    )

@assistants_router.route("/admin/cursor", methods=["GET"])
@token_required
async def list_assistants_admin_cursor():
    """
    # 获取数字助手列表 (管理员用)

    获取支持游标分页和过滤的数字助手列表，返回所有状态的助手。
    适用于后台管理系统的实现。

    ## 查询参数 (Query Parameters)

    * `cursor` (str, 可选): 下一页结果的游标。
    * `limit` (int, 可选): 每次请求返回的记录数。默认为 `10`。
    * `query` (str, 可选): 用于匹配助手名称或描述的搜索关键字。
    * `category` (str, 可选): 用于过滤助手列表的分类名称，匹配 categories 数组。
    * `tenant_id` (str, 可选): 租户ID，用于过滤特定租户的助手。如果不传则只返回公共(无租户)的助手。
    * `status` (int, 可选): 过滤助手状态，默认不传为全部状态。
    """
    cursor = request.args.get("cursor", None)
    limit = request.args.get("limit", 10, type=int)
    query = request.args.get("query", "")
    category = request.args.get("category", "")
    tenant_id = request.args.get("tenant_id", None)
    status_arg = request.args.get("status", None)
    status = int(status_arg) if status_arg is not None else None

    async with get_session() as session:
        assistant_service = AssistantService(session)
        result = await assistant_service.list_all_cursor(
            cursor=cursor,
            limit=limit,
            search=query if query else None,
            category=category if category else None,
            tenant_id=tenant_id,
            status=status
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
    """
    # 创建数字助手

    创建一个新的数字助手，支持上传提示词文件、头像和源文件。

    ## 表单数据 (Form Data)

    * `name` (str, 必填): 助手名称。
    * `profession` (str, 必填): 助手职业/角色。
    * `description` (str, 可选): 助手描述。
    * `defaultInitPrompt` 或 `default_init_prompt` (str, 可选): 默认的初始化提示词。
    * `tenantId` 或 `tenant_id` (str, 可选): 租户ID。
    * `sortOrder` 或 `sort_order` (int, 可选): 排序顺序，默认为0。
    * `status` (int, 可选): 助手状态，0表示审核中，1表示已发布。默认为0。
    * `categories` (str 或 list, 可选): 助手分类。可以是 JSON 字符串、逗号分隔的字符串或列表。
    * `skills` (逗号分隔的skill id UUID 数组, 可选): 助手技能。可以是 JSON 字符串、逗号分隔的skill id UUID 数组, 。
    * `prompt_file` (file, 可选): Markdown 格式的提示词文件 (.md)。
    * `avatar` (file, 可选): PNG 格式的头像文件 (.png)。
    * `source_url` (file, 可选): ZIP 格式的源文件压缩包 (.zip)。
    """
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
    source_url_file = files.get("source_url")

    # Validate files
    if prompt_file and not prompt_file.filename.endswith('.md'):
        raise BadRequestException(message="promptFile must be a .md file")

    if avatar_file and not avatar_file.filename.endswith('.png'):
        raise BadRequestException(message="avatar must be a .png file")

    if source_url_file and not source_url_file.filename.endswith('.zip'):
        raise BadRequestException(message="source_url must be a .zip file")

    # Pre-generate UUID for both storage and database
    assistant_id = str(uuid.uuid4())

    async with get_session() as session:
        assistant_service = AssistantService(session)

        # Check if name already exists
        existing = await assistant_service.get_by_name(req.name)
        if existing:
            raise BadRequestException(message="Assistant name already exists")

        # Check if we need to upload files
        has_files = prompt_file or avatar_file or source_url_file

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

            source_url_file_path = None
            source_url_object_key = None
            if source_url_file:
                source_url_file_path = os.path.join(temp_dir, source_url_file.filename)
                await source_url_file.save(source_url_file_path)
                source_url_object_key = f"assistant-hub/{assistant_id}/{source_url_file.filename}"

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

                    if source_url_file_path and source_url_object_key:
                        cos_client.upload_file(
                            bucket_name=bucket_name,
                            local_file_path=source_url_file_path,
                            object_key=source_url_object_key
                        )
                        req.source_url = source_url_object_key
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
                if source_url_file_path and os.path.exists(source_url_file_path):
                    os.remove(source_url_file_path)
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

@assistants_router.route("/<assistant_id>/approve", methods=["POST"])
@token_required
async def approve_assistant(assistant_id: str):
    """
    # 审批通过数字助手

    将处于审核中的数字助手状态更新为已上线 (status=1)。

    ## 路径参数 (Path Parameters)

    * `assistant_id` (str): 要审批的数字助手的唯一标识符 (UUID)。
    """
    async with get_session() as session:
        assistant_service = AssistantService(session)

        # 尝试更新状态
        assistant = await assistant_service.update(assistant_id, {"status": 1})
        if not assistant:
            raise NotFoundException(message="Assistant not found")

        assistant_dict = assistant.to_dict()

    return success_response(
        data=assistant_dict,
        message="Assistant approved successfully"
    )

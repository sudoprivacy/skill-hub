"""Skills management routes"""

import os
import uuid
import logging
from functools import wraps
from quart import Blueprint, request, current_app

from skill_hub.api.auth import token_required
from skill_hub.schemas.skill_schemas import SkillCreateRequest
from skill_hub.services.skill_service import SkillService
from skill_hub.services.skill_version_service import SkillVersionService
from skill_hub.db.database import get_session
from skill_hub.utils.object_storage_client import ObjectStorageClient
from skill_hub.api.responses import success_response
from skill_hub.api.exceptions import BadRequestException

logger = logging.getLogger(__name__)

skills_router = Blueprint("skills", __name__)

def map_request(f):
    """Decorator to map HTTP request to SkillCreateRequest object"""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        form_data = await request.form
        # Add tenant_id from args if not in form data but present in args, though usually it comes from auth/context
        # Let's keep it simple and just use form data for POST
        skill_request = SkillCreateRequest.from_form_data(form_data)
        
        is_valid, error = skill_request.validate()
        if not is_valid:
            raise BadRequestException(message=error)
            
        return await f(skill=skill_request, *args, **kwargs)
    return decorated_function

@skills_router.route("/cursor", methods=["GET"])
@token_required
async def list_skills_cursor():
    """
    # 获取技能列表 (游标分页)

    获取支持游标分页和过滤的技能列表。默认只返回已上线 (status=1) 的技能。
    适用于无限滚动/加载更多的实现。
    
    ## 查询参数 (Query Parameters)
    
    * `cursor` (str, 可选): 下一页结果的游标。
    * `limit` (int, 可选): 每次请求返回的记录数。默认为 `10`。
    * `query` (str, 可选): 用于匹配技能名称或描述的搜索关键字。
    * `categories` (str, 可选): 用于过滤技能列表的技能分类。
    
    ## 响应 (Returns)
    
    返回包含以下结构的 JSON 响应：
    
    ```json
    {
        "status": "success",
        "message": "Skills retrieved successfully",
        "data": {
            "skills": [
                {
                    "id": "uuid",
                    "name": "string",
                    "display_name": "string",
                    "description": "string",
                    "category": "string",
                    "categories": ["string"],
                    "core_features": "string",
                    "applicable_scenarios": "string",
                    "emoji": "string",
                    "homepage": "string",
                    "sort_order": "int",
                    "icon": "string",
                    "author_id": "string",
                    "is_active": true,
                    "created_at": "datetime",
                    "updated_at": "datetime"
                }
            ],
            "next_cursor": "string or null",
            "has_more": true
        }
    }
    ```
    """
    cursor = request.args.get("cursor", None)
    limit = request.args.get("limit", 10, type=int)
    query = request.args.get("query", "")
    categories = request.args.get("categories", "")
    tenant_id = request.args.get("tenant_id", None)

    async with get_session() as session:
        skill_service = SkillService(session)
        result = await skill_service.list_all_cursor(
            cursor=cursor,
            limit=limit,
            search=query if query else None,
            categories=categories if categories else None,
            tenant_id=tenant_id
        )
        
        # Convert objects to dicts for JSON serialization
        skills_data = [skill.to_dict() for skill in result["skills"]]

        result["skills"] = skills_data

    return success_response(
        data=result,
        message="Skills retrieved successfully"
    )

@skills_router.route("/<skill_id>", methods=["GET"])
@token_required
async def get_skill(skill_id: str):
    """
    # 获取技能详情

    获取指定技能的详细信息及其所有可用版本。默认返回的通常是已上线的技能。
    
    ## 路径参数 (Path Parameters)
    
    * `skill_id` (str): 要检索的技能的唯一标识符 (UUID)。
    
    ## 响应 (Returns)
    
    返回包含技能详情及其版本的 JSON 响应：
    
    ```json
    {
        "status": "success",
        "message": "Skill details retrieved successfully",
        "data": {
            "skill": {
                "id": "uuid",
                "name": "string",
                "display_name": "string",
                "description": "string",
                "category": "string",
                "categories": ["string"],
                "core_features": "string",
                "applicable_scenarios": "string",
                "emoji": "string",
                "homepage": "string",
                "sort_order": "int",
                "status": "int",
                "icon": "string",
                "author_id": "string",
                "is_active": true,
                "created_at": "datetime",
                "updated_at": "datetime"
            },
            "versions": [
                {
                    "id": "uuid",
                    "skill_id": "uuid",
                    "version": "string",
                    "source_url": "string",
                    "checksum": "string",
                    "changelog": "string",
                    "readme_content": "string",
                    "created_at": "datetime",
                    "updated_at": "datetime"
                }
            ]
        }
    }
    ```
    
    ## 异常 (Raises)
    
    * `BadRequestException`: 如果请求的 `skill_id` 在数据库中不存在 (400 Bad Request)。
    """
    async with get_session() as session:
        skill_service = SkillService(session)
        skill_version_service = SkillVersionService(session)
        
        # Get skill details
        skill = await skill_service.get_by_id(skill_id)
        if not skill:
            raise BadRequestException(message="Skill not found")
            
        # Get all versions for this skill, limit to a high number to get all of them or adjust pagination
        # We want to sort by version, so we specify sort_by="version" and sort_order="desc"
        versions_result = await skill_version_service.list_by_skill(
            skill_id=skill_id,
            page=1,
            per_page=100,  # Assuming a skill won't have more than 100 versions for now
            sort_by="version",
            sort_order="desc"
        )
        
        skill_data = skill.to_dict()
        versions_data = [v.to_dict() for v in versions_result["versions"]]
        
    return success_response(
        data={
            "skill": skill_data,
            "versions": versions_data
        },
        message="Skill details retrieved successfully"
    )

@skills_router.route("", methods=["POST"])
@token_required
@map_request
async def add_skill(skill: SkillCreateRequest):
    """
    # 添加/更新技能
    
    添加一个新技能或现有技能的新版本。包含文件上传功能。
    
    ## 表单数据 (Form Data)
    
    * `name` (str, 必填): 技能名称 (通常是英文标识符)。
    * `display_name` (str, 必填): 技能显示名称。
    * `version` (str, 必填): 技能版本号。
    * `category` (str, 可选): 技能的主要分类。
    * `categories` (list[str], 可选): 技能所属的多个分类数组。
    * `description` (str, 可选): 技能描述。
    * `core_features` (str, 可选): 技能的核心功能说明。
    * `applicable_scenarios` (str, 可选): 技能的适用场景。
    * `emoji` (str, 可选): 技能的 Emoji 图标。
    * `homepage` (str, 可选): 技能的主页链接。
    * `changelog` (str, 可选): 该版本的更新日志。
    * `author_id` (str, 可选): 作者 ID。
    * `sort_order` (int, 可选): 排序权重。
    * `status` (int, 可选): 技能状态，0表示审核中，1表示已上线。默认为0。

    ## 文件上传 (File Uploads)
    
    * `skill_file` (File, 必填): 包含技能代码的 .zip 文件。
    * `icon_file` (File, 可选): 技能图标的 .png 文件。
    
    ## 响应 (Returns)
    
    返回包含创建的技能及其版本信息的 JSON 响应：
    
    ```json
    {
        "status": "success",
        "message": "Skill added successfully",
        "data": {
            "skill": {
                "id": "uuid",
                "name": "string",
                "display_name": "string",
                "description": "string",
                "category": "string",
                "categories": ["string"],
                "core_features": "string",
                "applicable_scenarios": "string",
                "emoji": "string",
                "homepage": "string",
                "sort_order": "int",
                "status": "int",
                "icon": "string",
                "author_id": "string",
                "is_active": true,
                "created_at": "datetime",
                "updated_at": "datetime"
            },
            "version": {
                "id": "uuid",
                "skill_id": "uuid",
                "version": "string",
                "source_url": "string",
                "checksum": "string",
                "changelog": "string",
                "readme_content": "string",
                "created_at": "datetime",
                "updated_at": "datetime"
            }
        }
    }
    ```
    
    ## 异常 (Raises)
    
    * `BadRequestException`: 参数校验失败或文件上传错误。
    """
    files = await request.files
    skill_file = files.get("skill_file")
    icon_file = files.get("icon_file")
    
    if not skill_file:
        raise BadRequestException(message="skill_file is required")
    if not skill_file.filename.endswith('.zip'):
        raise BadRequestException(message="skill_file must be a .zip file")

    has_icon = False
    if icon_file:
        has_icon = True
        if not icon_file.filename.endswith('.png'):
            raise BadRequestException(message="icon_file must be a .png file")



    # Generate a UUID for the skill
    skill_id = str(uuid.uuid4())
    
    config = current_app.config.get("APP_CONFIG")
    upload_dir = getattr(config, "upload_dir", "data/uploads")
    
    # Save files temporarily
    temp_dir = os.path.join(upload_dir, "temp", skill_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    skill_file_path = os.path.join(temp_dir, skill_file.filename)
    if has_icon:
        icon_file_path = os.path.join(temp_dir, icon_file.filename)
    
    await skill_file.save(skill_file_path)

    if has_icon:
        await icon_file.save(icon_file_path)

    skill_object_key = f"skill-hub/{skill_id}/{skill_file.filename}"
    if has_icon:
        icon_object_key = f"skill-hub/{skill_id}/icon.png"


    
    # Upload to Object Storage
    try:
        cos_client = ObjectStorageClient(config)
        if cos_client.client:
            bucket_name = "sudoclaw-1309794936"
            cos_client.upload_file(
                bucket_name=bucket_name,
                local_file_path=skill_file_path,
                object_key=skill_object_key
            )
            if has_icon:
                cos_client.upload_file(
                    bucket_name=bucket_name,
                    local_file_path=icon_file_path,
                    object_key=icon_object_key
                )
        else:
            logger.warning("ObjectStorageClient is not initialized")
    except Exception as e:
        logger.error(f"Error uploading to object storage: {str(e)}")
        raise BadRequestException(message=f"Failed to upload files: {str(e)}")

    # Delete temp files
    try:
        os.remove(skill_file_path)
        if has_icon:
            os.remove(icon_file_path)
        os.rmdir(temp_dir)
    except Exception as e:
        logger.warning(f"Failed to cleanup temp files: {str(e)}")

    async with get_session() as session:
        skill_service = SkillService(session)
        skill_version_service = SkillVersionService(session)

        author_id = ""
        skill_data = skill.to_skill_data(author_id)

        if has_icon:
            skill_data["icon"] = icon_object_key

        # Create or update skill
        existing_skill = await skill_service.get_by_name(skill.name, skill.tenant_id)
        if not existing_skill:
            # Overwrite id to be our generated skill_id
            skill_data["id"] = skill_id
            db_skill = await skill_service.create(skill_data)
        else:
            db_skill = existing_skill
            skill_id = str(db_skill.id)

        # Check if version exists
        existing_version = await skill_version_service.get_by_skill_and_version(skill_id, skill.version)
        if existing_version:
            raise BadRequestException(message=f"Version {skill.version} already exists for skill {skill.name}")

        checksum = ""
        
        version_data = skill.to_version_data(
            skill_id=skill_id,
            source_url=skill_object_key,
            checksum=checksum
        )

        db_version = await skill_version_service.create(version_data)

    return success_response(
        data={
            "skill": db_skill.to_dict(),
            "version": db_version.to_dict()
        },
        message="Skill added successfully"
    )

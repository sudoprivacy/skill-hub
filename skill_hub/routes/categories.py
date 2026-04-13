"""Categories management routes"""

import logging
from quart import Blueprint, request

from skill_hub.api.auth import token_required
from skill_hub.schemas.category_schemas import CategoryCreateRequest, CategoryUpdateRequest
from skill_hub.services.category_service import CategoryService
from skill_hub.db.database import get_session
from skill_hub.api.responses import success_response
from skill_hub.api.exceptions import BadRequestException, NotFoundException

logger = logging.getLogger(__name__)

categories_router = Blueprint("categories", __name__)

@categories_router.route("", methods=["GET"])
@token_required
async def list_categories():
    """Get list of categories"""
    type_filter = request.args.get("type", default=0, type=int)

    async with get_session() as session:
        category_service = CategoryService(session)
        categories = await category_service.list_all(type_filter=type_filter)
        categories_data = [c.to_dict() for c in categories]

    return success_response(
        data=categories_data,
        message="Categories retrieved successfully"
    )

@categories_router.route("/<category_id>", methods=["GET"])
@token_required
async def get_category(category_id: str):
    """Get category by ID"""
    async with get_session() as session:
        category_service = CategoryService(session)
        category = await category_service.get_by_id(category_id)
        if not category:
            raise NotFoundException(message="Category not found")
            
    return success_response(
        data=category.to_dict(),
        message="Category retrieved successfully"
    )

@categories_router.route("", methods=["POST"])
@token_required
async def create_category():
    """Create a new category"""
    data = await request.get_json()
    if not data:
        raise BadRequestException(message="Invalid JSON payload")
        
    req = CategoryCreateRequest.from_dict(data)
    is_valid, error = req.validate()
    if not is_valid:
        raise BadRequestException(message=error)
        
    async with get_session() as session:
        category_service = CategoryService(session)
        
        # Check if already exists for this specific type
        existing = await category_service.get_by_name_and_type(req.name, req.type)
        if existing:
            raise BadRequestException(message="Category name already exists for this type")
            
        category = await category_service.create(req.to_category_data())
        category_dict = category.to_dict()
        
    return success_response(
        data=category_dict,
        message="Category created successfully",
        status_code=201
    )

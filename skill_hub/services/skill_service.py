"""Skill service for database CRUD operations"""

import os
import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from skill_hub.models.skill import Skill
from skill_hub.api.exceptions import NotFoundException, ConflictException

logger = logging.getLogger(__name__)

# Default path (relative to the COS base URL) of the fallback icon used when a
# skill record does not provide one.
_DEFAULT_ICON_PATH = "skill-hub/icons/default.png"


def _get_cos_base_url() -> str:
    """Resolve the public base URL for COS-hosted assets.

    The value is read from the ``SKILL_HUB_COS_BASE_URL`` environment variable
    (also exposed via :class:`skill_hub.config.config.Config.cos_base_url`).
    Any trailing slash is stripped so callers can safely concatenate with an
    object key using ``f"{base_url}/{key}"``.
    """
    base_url = os.getenv("SKILL_HUB_COS_BASE_URL", "").strip()
    if not base_url:
        logger.warning(
            "SKILL_HUB_COS_BASE_URL is not configured; skill icon URLs will be "
            "returned as relative paths."
        )
    return base_url.rstrip("/")


class SkillService:
    """Service for managing skill CRUD operations"""
    
    def __init__(self, session: AsyncSession):
        """Initialize the skill service
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def create(self, skill_data: Dict[str, Any]) -> Skill:
        """Create a new skill
        
        Args:
            skill_data: Skill data dictionary
            
        Returns:
            Created skill
            
        Raises:
            ConflictException: If skill with same name already exists
        """
        # Check if skill with same name already exists
        existing = await self.get_by_name(skill_data.get("name"))
        if existing:
            raise ConflictException(
                message=f"Skill with name '{skill_data['name']}' already exists"
            )
        
        # Create skill instance
        skill = Skill.from_dict(skill_data)
        
        # Set timestamps if not provided
        if not skill.created_at:
            skill.created_at = datetime.utcnow()
        if not skill.updated_at:
            skill.updated_at = datetime.utcnow()
        
        # Save to database
        self.session.add(skill)
        await self.session.commit()
        await self.session.refresh(skill)
        
        return skill
    
    async def get_by_id(self, skill_id: str) -> Optional[Skill]:
        """Get skill by ID
        
        Args:
            skill_id: Skill ID (UUID string)
            
        Returns:
            Skill if found, None otherwise
        """
        try:
            skill_uuid = uuid.UUID(skill_id)
        except ValueError:
            return None
        
        stmt = select(Skill).where(Skill.id == skill_uuid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Skill]:
        """Get skill by name
        
        Args:
            name: Skill name
            
        Returns:
            Skill if found, None otherwise
        """
        stmt = select(Skill).where(Skill.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_all_cursor(
        self,
        cursor: Optional[str] = None,
        limit: int = 10,
        categories: Optional[str] = None,
        author_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """List skills with cursor-based pagination
        
        Args:
            cursor: Cursor string (base64 encoded datetime or id)
            limit: Items per page
            category_id: Filter by category ID
            author_id: Filter by author ID
            search: Search in name, display_name, and description
            
        Returns:
            Dictionary with skills, next_cursor, and has_more
        """
        import base64
        import json
        
        # Build query
        stmt = select(Skill).where(Skill.status == 1)
                
        if categories:
            # Query if the string value is present in the categories array
            stmt = stmt.where(Skill.categories.any(categories))
            
        if author_id:
            try:
                author_uuid = uuid.UUID(author_id)
                stmt = stmt.where(Skill.author_id == author_uuid)
            except ValueError:
                return {"skills": [], "next_cursor": None, "has_more": False}
                
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                (Skill.name.ilike(search_pattern)) |
                (Skill.display_name.ilike(search_pattern)) |
                (Skill.description.ilike(search_pattern))
            )
            
        # Parse cursor
        cursor_data = None
        if cursor:
            try:
                # Add padding if needed
                padding_needed = len(cursor) % 4
                if padding_needed:
                    cursor += '=' * (4 - padding_needed)
                decoded = base64.b64decode(cursor).decode('utf-8')
                cursor_data = json.loads(decoded)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to decode cursor: {e}")
                pass
                
        import sqlalchemy
        
        if cursor_data:
            cursor_sort = int(cursor_data.get('sort_order', 0)) if cursor_data.get('sort_order') is not None else 0
            cursor_id = cursor_data['id']
            
            # Keyset pagination logic for sort_order DESC, id DESC
            # sort_order < cursor_sort OR (sort_order = cursor_sort AND id < cursor_id)
            # using coalesce to handle NULLs properly
            sort_order_col = func.coalesce(Skill.sort_order, 0)
            stmt = stmt.where(
                (sort_order_col < cursor_sort) |
                ((sort_order_col == cursor_sort) & (func.cast(Skill.id, sqlalchemy.String) < cursor_id))
            )
            
        # Order by sort_order DESC, id DESC
        stmt = stmt.order_by(desc(func.coalesce(Skill.sort_order, 0)), desc(func.cast(Skill.id, sqlalchemy.String)))
        
        # Fetch limit + 1 to determine if there are more
        stmt = stmt.limit(limit + 1)
        
        result = await self.session.execute(stmt)
        skills = result.scalars().all()
        
        # Clone skills to avoid modifying SQLAlchemy models directly
        import copy
        cloned_skills = []
        for skill in skills:
            # We can't deepcopy sqlalchemy models easily, so we convert to dict and create a new object or just copy the attributes we need
            # but since we're returning models usually, let's create a superficial clone
            skill_dict = {c.name: getattr(skill, c.name) for c in skill.__table__.columns}
            cloned_skill = Skill(**skill_dict)
            cloned_skills.append(cloned_skill)
            
        # Replace empty icon with default. The base URL is sourced from the
        # SKILL_HUB_COS_BASE_URL env var (see .env.example / Config) rather
        # than being hardcoded here.
        base_url = _get_cos_base_url()
        default_icon = _DEFAULT_ICON_PATH
        for skill in cloned_skills:
            icon_path = skill.icon if skill.icon else default_icon
            skill.icon = f"{base_url}/{icon_path}" if base_url else icon_path
                
        has_more = len(cloned_skills) > limit
        if has_more:
            cloned_skills = cloned_skills[:limit]
            
        next_cursor = None
        if cloned_skills:
            last_skill = cloned_skills[-1]
            last_sort = last_skill.sort_order if last_skill.sort_order is not None else 0
            last_id = str(last_skill.id)
            cursor_dict = {"sort_order": last_sort, "id": last_id}
            next_cursor = base64.b64encode(json.dumps(cursor_dict).encode('utf-8')).decode('utf-8')
            
        return {
            "skills": cloned_skills,
            "next_cursor": next_cursor,
            "has_more": has_more
        }

    async def list_all(
        self,
        page: int = 1,
        per_page: int = 10,
        categories: Optional[str] = None,
        author_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """List skills with pagination and filtering
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            categories: Filter by category
            author_id: Filter by author ID
            search: Search in name, display_name, and description
            sort_by: Field to sort by (name, display_name, star_count, created_at)
            sort_order: Sort order (asc or desc)
            
        Returns:
            Dictionary with skills and pagination info
        """
        # Build query
        stmt = select(Skill).where(Skill.status != 0)
        
        # Apply filters
            
        if categories:
            stmt = stmt.where(Skill.categories.any(categories))
        
        if author_id:
            try:
                author_uuid = uuid.UUID(author_id)
                stmt = stmt.where(Skill.author_id == author_uuid)
            except ValueError:
                # Invalid UUID, return empty result
                return {
                    "skills": [],
                    "total": 0,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": 0,
                }
        
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                (Skill.name.ilike(search_pattern)) |
                (Skill.display_name.ilike(search_pattern)) |
                (Skill.description.ilike(search_pattern))
            )
        
        # Apply sorting
        sort_column = getattr(Skill, sort_by, Skill.sort_order)
        if sort_order.lower() == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(sort_column)
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar()
        
        # Apply pagination
        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)
        
        # Execute query
        result = await self.session.execute(stmt)
        skills = result.scalars().all()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        
        return {
            "skills": skills,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
    
    async def update(self, skill_id: str, update_data: Dict[str, Any]) -> Optional[Skill]:
        """Update a skill
        
        Args:
            skill_id: Skill ID (UUID string)
            update_data: Data to update
            
        Returns:
            Updated skill if found, None otherwise
            
        Raises:
            ConflictException: If trying to update to a name that already exists
        """
        # Get existing skill
        skill = await self.get_by_id(skill_id)
        if not skill:
            return None
        
        # Check if name is being changed and if new name already exists
        if "name" in update_data and update_data["name"] != skill.name:
            existing = await self.get_by_name(update_data["name"])
            if existing and existing.id != skill.id:
                raise ConflictException(
                    message=f"Skill with name '{update_data['name']}' already exists"
                )
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(skill, key) and key not in ["id", "created_at"]:
                setattr(skill, key, value)
        
        # Update timestamp
        skill.updated_at = datetime.utcnow()
        
        # Save changes
        await self.session.commit()
        await self.session.refresh(skill)
        
        return skill
    
    async def delete(self, skill_id: str) -> bool:
        """Delete a skill
        
        Args:
            skill_id: Skill ID (UUID string)
            
        Returns:
            True if deleted, False if not found
        """
        skill = await self.get_by_id(skill_id)
        if not skill:
            return False
        
        await self.session.delete(skill)
        await self.session.commit()
        
        return True
    
    async def increment_star_count(self, skill_id: str) -> Optional[Skill]:
        """Increment star count for a skill
        
        Args:
            skill_id: Skill ID (UUID string)
            
        Returns:
            Updated skill if found, None otherwise
        """
        skill = await self.get_by_id(skill_id)
        if not skill:
            return None
        
        skill.star_count += 1
        skill.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(skill)
        
        return skill
    
    async def decrement_star_count(self, skill_id: str) -> Optional[Skill]:
        """Decrement star count for a skill
        
        Args:
            skill_id: Skill ID (UUID string)
            
        Returns:
            Updated skill if found, None otherwise
        """
        skill = await self.get_by_id(skill_id)
        if not skill:
            return None
        
        if skill.star_count > 0:
            skill.star_count -= 1
            skill.updated_at = datetime.utcnow()
            
            await self.session.commit()
            await self.session.refresh(skill)
        
        return skill
    
    async def get_categories(self) -> List[str]:
        """Get list of all categories ordered by count descending
        
        Returns:
            List of unique categories
        """
        stmt = (
            select(Skill.category)
            .where(Skill.category.isnot(None))
            .where(Skill.category != "")
            .group_by(Skill.category)
            .order_by(desc(func.count(Skill.id)))
        )
        result = await self.session.execute(stmt)
        categories = result.scalars().all()
        
        return [cat for cat in categories if cat]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get skill statistics
        
        Returns:
            Dictionary with statistics
        """
        # Total skills count
        total_stmt = select(func.count()).select_from(Skill)
        total = (await self.session.execute(total_stmt)).scalar()
        
        # Total stars count
        stars_stmt = select(func.sum(Skill.star_count))
        total_stars = (await self.session.execute(stars_stmt)).scalar() or 0
        
        # Skills per category
        category_stmt = (
            select(Skill.category, func.count().label("count"))
            .where(Skill.category.isnot(None))
            .group_by(Skill.category)
        )
        category_result = await self.session.execute(category_stmt)
        categories = {
            row.category: row.count
            for row in category_result
            if row.category
        }
        
        # Recent skills (last 7 days)
        week_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = week_ago.replace(day=week_ago.day - 7)
        
        recent_stmt = select(func.count()).where(Skill.created_at >= week_ago)
        recent = (await self.session.execute(recent_stmt)).scalar()
        
        return {
            "total_skills": total,
            "total_stars": total_stars,
            "average_stars": total_stars / total if total > 0 else 0,
            "categories": categories,
            "recent_skills_7d": recent,
        }

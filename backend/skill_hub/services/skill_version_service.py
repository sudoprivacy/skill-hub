"""Skill Version service for database CRUD operations"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from skill_hub.models.skill_version import SkillVersion
from skill_hub.api.exceptions import NotFoundException, ConflictException


class SkillVersionService:
    """Service for managing skill version CRUD operations"""
    
    def __init__(self, session: AsyncSession):
        """Initialize the skill version service
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def create(self, version_data: Dict[str, Any]) -> SkillVersion:
        """Create a new skill version
        
        Args:
            version_data: Skill version data dictionary
            
        Returns:
            Created skill version
            
        Raises:
            ConflictException: If version with same skill_id and version already exists
        """
        # Check if version with same skill_id and version already exists
        existing = await self.get_by_skill_and_version(
            version_data.get("skill_id"),
            version_data.get("version")
        )
        if existing:
            raise ConflictException(
                message=f"Version '{version_data['version']}' already exists for skill {version_data['skill_id']}"
            )
        
        # Create skill version instance
        version = SkillVersion.from_dict(version_data)
        
        # Set timestamps if not provided
        if not version.created_at:
            version.created_at = datetime.utcnow()
        if not version.updated_at:
            version.updated_at = datetime.utcnow()
        
        # Save to database
        self.session.add(version)
        await self.session.commit()
        await self.session.refresh(version)
        
        return version
    
    async def get_by_id(self, version_id: str) -> Optional[SkillVersion]:
        """Get skill version by ID
        
        Args:
            version_id: Skill version ID (UUID string)
            
        Returns:
            Skill version if found, None otherwise
        """
        try:
            version_uuid = uuid.UUID(version_id)
        except ValueError:
            return None
        
        stmt = select(SkillVersion).where(SkillVersion.id == version_uuid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_skill_and_version(self, skill_id: str, version: str) -> Optional[SkillVersion]:
        """Get skill version by skill ID and version
        
        Args:
            skill_id: Skill ID (UUID string)
            version: Version string
            
        Returns:
            Skill version if found, None otherwise
        """
        try:
            skill_uuid = uuid.UUID(skill_id)
        except ValueError:
            return None
        
        stmt = select(SkillVersion).where(
            (SkillVersion.skill_id == skill_uuid) &
            (SkillVersion.version == version)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_by_skill(
        self,
        skill_id: str,
        page: int = 1,
        per_page: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """List skill versions for a specific skill with pagination
        
        Args:
            skill_id: Skill ID (UUID string)
            page: Page number (1-indexed)
            per_page: Items per page
            sort_by: Field to sort by (version, created_at, updated_at)
            sort_order: Sort order (asc or desc)
            
        Returns:
            Dictionary with skill versions and pagination info
        """
        try:
            skill_uuid = uuid.UUID(skill_id)
        except ValueError:
            # Invalid UUID, return empty result
            return {
                "versions": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
            }
        
        # Build query
        stmt = select(SkillVersion).where(SkillVersion.skill_id == skill_uuid)
        
        # Apply sorting
        sort_column = getattr(SkillVersion, sort_by, SkillVersion.created_at)
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
        versions = result.scalars().all()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        
        return {
            "versions": versions,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
    
    async def list_all(
        self,
        page: int = 1,
        per_page: int = 10,
        skill_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """List all skill versions with pagination and filtering
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            skill_id: Filter by skill ID
            search: Search in version, changelog, and readme_content
            sort_by: Field to sort by (version, created_at, updated_at)
            sort_order: Sort order (asc or desc)
            
        Returns:
            Dictionary with skill versions and pagination info
        """
        # Build query
        stmt = select(SkillVersion)
        
        # Apply filters
        if skill_id:
            try:
                skill_uuid = uuid.UUID(skill_id)
                stmt = stmt.where(SkillVersion.skill_id == skill_uuid)
            except ValueError:
                # Invalid UUID, return empty result
                return {
                    "versions": [],
                    "total": 0,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": 0,
                }
        
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                (SkillVersion.version.ilike(search_pattern)) |
                (SkillVersion.changelog.ilike(search_pattern)) |
                (SkillVersion.readme_content.ilike(search_pattern))
            )
        
        # Apply sorting
        sort_column = getattr(SkillVersion, sort_by, SkillVersion.created_at)
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
        versions = result.scalars().all()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        
        return {
            "versions": versions,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }
    
    async def update(self, version_id: str, update_data: Dict[str, Any]) -> Optional[SkillVersion]:
        """Update a skill version
        
        Args:
            version_id: Skill version ID (UUID string)
            update_data: Data to update
            
        Returns:
            Updated skill version if found, None otherwise
            
        Raises:
            ConflictException: If trying to update to a version that already exists for the same skill
        """
        # Get existing version
        version = await self.get_by_id(version_id)
        if not version:
            return None
        
        # Check if version is being changed and if new version already exists for the same skill
        if "version" in update_data and update_data["version"] != version.version:
            existing = await self.get_by_skill_and_version(
                str(version.skill_id),
                update_data["version"]
            )
            if existing and existing.id != version.id:
                raise ConflictException(
                    message=f"Version '{update_data['version']}' already exists for skill {version.skill_id}"
                )
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(version, key) and key not in ["id", "skill_id", "created_at"]:
                setattr(version, key, value)
        
        # Update timestamp
        version.updated_at = datetime.utcnow()
        
        # Save changes
        await self.session.commit()
        await self.session.refresh(version)
        
        return version
    
    async def delete(self, version_id: str) -> bool:
        """Delete a skill version
        
        Args:
            version_id: Skill version ID (UUID string)
            
        Returns:
            True if deleted, False if not found
        """
        version = await self.get_by_id(version_id)
        if not version:
            return False
        
        await self.session.delete(version)
        await self.session.commit()
        
        return True
    
    async def get_latest_version(self, skill_id: str) -> Optional[SkillVersion]:
        """Get the latest version for a skill
        
        Args:
            skill_id: Skill ID (UUID string)
            
        Returns:
            Latest skill version if found, None otherwise
        """
        try:
            skill_uuid = uuid.UUID(skill_id)
        except ValueError:
            return None
        
        stmt = select(SkillVersion).where(
            SkillVersion.skill_id == skill_uuid
        ).order_by(
            desc(SkillVersion.created_at)
        ).limit(1)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_version_count(self, skill_id: str) -> int:
        """Get the number of versions for a skill
        
        Args:
            skill_id: Skill ID (UUID string)
            
        Returns:
            Number of versions
        """
        try:
            skill_uuid = uuid.UUID(skill_id)
        except ValueError:
            return 0
        
        stmt = select(func.count()).where(SkillVersion.skill_id == skill_uuid)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get skill version statistics
        
        Returns:
            Dictionary with statistics
        """
        # Total versions count
        total_stmt = select(func.count()).select_from(SkillVersion)
        total = (await self.session.execute(total_stmt)).scalar()
        
        # Versions per skill
        skill_stmt = (
            select(SkillVersion.skill_id, func.count().label("count"))
            .group_by(SkillVersion.skill_id)
        )
        skill_result = await self.session.execute(skill_stmt)
        versions_per_skill = {
            str(row.skill_id): row.count
            for row in skill_result
        }
        
        # Recent versions (last 7 days)
        week_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = week_ago.replace(day=week_ago.day - 7)
        
        recent_stmt = select(func.count()).where(
            SkillVersion.created_at >= week_ago
        )
        recent = (await self.session.execute(recent_stmt)).scalar()
        
        return {
            "total_versions": total,
            "versions_per_skill": versions_per_skill,
            "recent_versions_7d": recent,
            "average_versions_per_skill": total / len(versions_per_skill) if versions_per_skill else 0,
        }
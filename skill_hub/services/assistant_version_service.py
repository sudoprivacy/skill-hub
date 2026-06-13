"""Assistant Version service for database CRUD operations"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from skill_hub.api.exceptions import ConflictException
from skill_hub.models.assistant_version import AssistantVersion


class AssistantVersionService:
    """Service for managing assistant version records."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, version_data: Dict[str, Any]) -> AssistantVersion:
        existing = await self.get_by_assistant_and_version(
            version_data.get("assistant_id"),
            version_data.get("version"),
        )
        if existing:
            raise ConflictException(
                message=f"Version '{version_data['version']}' already exists for assistant {version_data['assistant_id']}"
            )

        version = AssistantVersion.from_dict(version_data)
        if not version.created_at:
            version.created_at = datetime.utcnow()
        if not version.updated_at:
            version.updated_at = datetime.utcnow()

        self.session.add(version)
        await self.session.commit()
        await self.session.refresh(version)
        return version

    async def get_by_id(self, version_id: str) -> Optional[AssistantVersion]:
        try:
            version_uuid = uuid.UUID(version_id)
        except ValueError:
            return None

        stmt = select(AssistantVersion).where(AssistantVersion.id == version_uuid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_assistant_and_version(self, assistant_id: str, version: str) -> Optional[AssistantVersion]:
        try:
            assistant_uuid = uuid.UUID(str(assistant_id))
        except (TypeError, ValueError):
            return None

        stmt = select(AssistantVersion).where(
            (AssistantVersion.assistant_id == assistant_uuid)
            & (AssistantVersion.version == version)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_version(self, assistant_id: str) -> Optional[AssistantVersion]:
        try:
            assistant_uuid = uuid.UUID(str(assistant_id))
        except (TypeError, ValueError):
            return None

        stmt = (
            select(AssistantVersion)
            .where(AssistantVersion.assistant_id == assistant_uuid)
            .order_by(desc(AssistantVersion.created_at))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_assistant(
        self,
        assistant_id: str,
        page: int = 1,
        per_page: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        try:
            assistant_uuid = uuid.UUID(str(assistant_id))
        except (TypeError, ValueError):
            return {"versions": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0}

        stmt = select(AssistantVersion).where(AssistantVersion.assistant_id == assistant_uuid)
        sort_column = getattr(AssistantVersion, sort_by, AssistantVersion.created_at)
        stmt = stmt.order_by(desc(sort_column) if sort_order.lower() == "desc" else sort_column)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar()

        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)
        result = await self.session.execute(stmt)
        versions = result.scalars().all()

        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        return {
            "versions": versions,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }

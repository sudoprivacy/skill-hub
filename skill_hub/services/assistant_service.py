"""Assistant service"""

import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.orm import selectinload

from skill_hub.models.assistant import Assistant
from skill_hub.models.assistant_version import AssistantVersion
from skill_hub.utils.tenant_utils import (
    synchronize_tenant_data,
    tenant_filter,
    tenants_filter,
)

class AssistantService:
    """Service for managing assistants"""
    
    def __init__(self, session: AsyncSession):
        """Initialize service with database session"""
        self.session = session
        
    async def get_by_id(self, assistant_id: str) -> Optional[Assistant]:
        """Get assistant by ID
        
        Args:
            assistant_id: Assistant UUID
            
        Returns:
            Assistant if found, None otherwise
        """
        try:
            if isinstance(assistant_id, str):
                assistant_uuid = uuid.UUID(assistant_id)
            else:
                assistant_uuid = assistant_id
                
            query = select(Assistant).options(selectinload(Assistant.versions)).where(Assistant.id == assistant_uuid)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except ValueError:
            return None
            
    async def get_by_name(
        self,
        name: str,
        tenant_id: Optional[str] = None,
        tenant_ids: Optional[List[str]] = None,
    ) -> Optional[Assistant]:
        """Get assistant by name
        
        Args:
            name: Assistant name
            
        Returns:
            Assistant if found, None otherwise
        """
        query = select(Assistant).where(Assistant.name == name)
        if tenant_id is not None or tenant_ids is not None:
            query = query.where(tenants_filter(Assistant, tenant_ids, tenant_id))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def list_all(self, tenant_id: Optional[str] = None) -> List[Assistant]:
        """Get all assistants, optionally filtered by tenant

        Args:
            tenant_id: Optional tenant ID to filter by. If None, filters for assistants with no tenant_id

        Returns:
            List of Assistant objects
        """
        query = select(Assistant).options(selectinload(Assistant.versions))

        query = query.where(tenant_filter(Assistant, tenant_id))

        query = query.where(Assistant.status == 1)

        query = query.order_by(desc(Assistant.sort_order), desc(Assistant.created_at))
        result = await self.session.execute(query)

        assistants = list(result.scalars().all())
        return self._format_assistants(assistants)

    async def list_all_cursor(
        self,
        cursor: Optional[str] = None,
        limit: int = 10,
        category: Optional[str] = None,
        search: Optional[str] = None,
        tenant_id: Optional[str] = None,
        status: Optional[int] = 1
    ) -> Dict[str, Any]:
        """List assistants with cursor-based pagination

        Args:
            cursor: Cursor string (base64 encoded datetime or id)
            limit: Items per page
            category: Filter by category name in categories array
            search: Search in name, profession, and description
            tenant_id: Optional tenant ID to filter by. If None, filters for assistants with no tenant_id
            status: Filter by status. None means all statuses. Default is 1 (online).

        Returns:
            Dictionary with assistants, next_cursor, and has_more
        """
        import base64
        import json
        import sqlalchemy

        query = select(Assistant).options(selectinload(Assistant.versions))

        if category:
            query = query.where(Assistant.categories.any(category))

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (Assistant.name.ilike(search_pattern)) |
                (Assistant.profession.ilike(search_pattern)) |
                (Assistant.description.ilike(search_pattern))
            )

        query = query.where(tenant_filter(Assistant, tenant_id))

        if status is not None:
            query = query.where(Assistant.status == status)

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

        if cursor_data:
            cursor_sort_order = cursor_data.get('sort_order', 0)
            cursor_created_at = cursor_data['created_at']
            cursor_id = cursor_data['id']

            # Keyset pagination logic for sort_order DESC, created_at DESC, id DESC
            query = query.where(
                (Assistant.sort_order < cursor_sort_order) |
                ((Assistant.sort_order == cursor_sort_order) & (func.cast(Assistant.created_at, sqlalchemy.String) < cursor_created_at)) |
                ((Assistant.sort_order == cursor_sort_order) & (func.cast(Assistant.created_at, sqlalchemy.String) == cursor_created_at) & (func.cast(Assistant.id, sqlalchemy.String) < cursor_id))
            )

        # Order by sort_order DESC, created_at DESC, id DESC
        query = query.order_by(
            desc(Assistant.sort_order),
            desc(Assistant.created_at),
            desc(func.cast(Assistant.id, sqlalchemy.String))
        )

        # Fetch limit + 1 to determine if there are more
        query = query.limit(limit + 1)

        result = await self.session.execute(query)
        assistants = list(result.scalars().all())

        has_more = len(assistants) > limit
        if has_more:
            assistants = assistants[:limit]

        # Format assistants (CDN URLs)
        formatted_assistants = self._format_assistants(assistants)
        await self._attach_latest_versions(formatted_assistants)

        next_cursor = None
        if has_more and formatted_assistants:
            last_assistant = formatted_assistants[-1]
            last_sort_order = last_assistant.sort_order
            last_created = last_assistant.created_at.isoformat() if last_assistant.created_at else ""
            last_id = str(last_assistant.id)
            cursor_dict = {"sort_order": last_sort_order, "created_at": last_created, "id": last_id}
            next_cursor = base64.b64encode(json.dumps(cursor_dict).encode('utf-8')).decode('utf-8')

        return {
            "assistants": formatted_assistants,
            "next_cursor": next_cursor,
            "has_more": has_more
        }

    async def _attach_latest_versions(self, assistants: List[Assistant]) -> None:
        """Attach latest assistant_versions records to assistant objects."""
        assistant_ids = [assistant.id for assistant in assistants if assistant.id]
        if not assistant_ids:
            return

        stmt = (
            select(AssistantVersion)
            .where(AssistantVersion.assistant_id.in_(assistant_ids))
            .order_by(AssistantVersion.assistant_id, desc(AssistantVersion.created_at))
        )
        result = await self.session.execute(stmt)

        latest_versions = {}
        for version in result.scalars().all():
            key = str(version.assistant_id)
            if key not in latest_versions:
                latest_versions[key] = version

        for assistant in assistants:
            latest = latest_versions.get(str(assistant.id))
            if latest:
                set_committed_value(assistant, "versions", [latest])

    def _format_assistants(self, assistants: List[Assistant]) -> List[Assistant]:
        """Format assistant data, resolving avatar, prompt_file and source_url
        object keys to absolute URLs.

        In local content mode (SKILL_HUB_CONTENT_BASE_URL set) keys resolve to
        this hub's local content route; otherwise they are prefixed with the
        COS base URL (unchanged historical behavior).
        """
        import copy
        from skill_hub.utils.content_storage import is_local_mode, resolve_local_only, cos_base_url

        formatted_assistants = []
        base_url = cos_base_url()
        local = is_local_mode()

        def _resolve(value):
            if not value or value.startswith('http'):
                return value
            if local:
                return resolve_local_only(value)
            return f"{base_url}/{value}"

        for assistant in assistants:
            # Clone to avoid modifying original SQLAlchemy object state
            ast_dict = {c.name: getattr(assistant, c.name) for c in assistant.__table__.columns}

            # Make sure we're getting the list of skills correctly mapped to our Pydantic model response
            if 'skills' in ast_dict and ast_dict['skills']:
                ast_dict['skills'] = [str(s) for s in ast_dict['skills']]

            cloned = Assistant(**ast_dict)
            if hasattr(assistant, "versions"):
                set_committed_value(cloned, "versions", assistant.versions)

            cloned.avatar = _resolve(cloned.avatar)
            cloned.prompt_file = _resolve(cloned.prompt_file)

            formatted_assistants.append(cloned)

        return formatted_assistants
        
    async def create(self, data: Dict[str, Any]) -> Assistant:
        """Create a new assistant
        
        Args:
            data: Assistant data
            
        Returns:
            Created Assistant
        """
        synchronize_tenant_data(data)
        assistant = Assistant(**data)
        self.session.add(assistant)
        await self.session.commit()
        await self.session.refresh(assistant)
        return assistant
        
    async def update(self, assistant_id: str, data: Dict[str, Any]) -> Optional[Assistant]:
        """Update an assistant
        
        Args:
            assistant_id: Assistant UUID
            data: Data to update
            
        Returns:
            Updated Assistant if found, None otherwise
        """
        try:
            if isinstance(assistant_id, str):
                assistant_uuid = uuid.UUID(assistant_id)
            else:
                assistant_uuid = assistant_id
                
            # First check if exists
            assistant = await self.get_by_id(assistant_uuid)
            if not assistant:
                return None
                
            synchronize_tenant_data(data)

            # Update fields
            for key, value in data.items():
                if hasattr(assistant, key):
                    setattr(assistant, key, value)
                    
            await self.session.commit()
            await self.session.refresh(assistant)
            return assistant
            
        except ValueError:
            return None
            
    async def delete(self, assistant_id: str) -> bool:
        """Delete an assistant
        
        Args:
            assistant_id: Assistant UUID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            if isinstance(assistant_id, str):
                assistant_uuid = uuid.UUID(assistant_id)
            else:
                assistant_uuid = assistant_id
                
            assistant = await self.get_by_id(assistant_uuid)
            if not assistant:
                return False
                
            await self.session.delete(assistant)
            await self.session.commit()
            return True
            
        except ValueError:
            return False

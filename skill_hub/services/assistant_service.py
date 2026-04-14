"""Assistant service"""

import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from skill_hub.models.assistant import Assistant

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
                
            query = select(Assistant).where(Assistant.id == assistant_uuid)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except ValueError:
            return None
            
    async def get_by_name(self, name: str) -> Optional[Assistant]:
        """Get assistant by name
        
        Args:
            name: Assistant name
            
        Returns:
            Assistant if found, None otherwise
        """
        query = select(Assistant).where(Assistant.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
        
    async def list_all(self, category_id: Optional[str] = None, tenant_id: Optional[str] = None) -> List[Assistant]:
        """Get all assistants, optionally filtered by category and tenant

        Args:
            category_id: Optional UUID of the category to filter by
            tenant_id: Optional tenant ID to filter by. If None, filters for assistants with no tenant_id

        Returns:
            List of Assistant objects
        """
        query = select(Assistant)

        if category_id is not None:
            try:
                cat_uuid = uuid.UUID(category_id)
                query = query.where(Assistant.category_id == cat_uuid)
            except ValueError:
                # Invalid UUID, return empty list
                return []

        if tenant_id is not None:
            query = query.where(Assistant.tenant_id == tenant_id)
        else:
            query = query.where(Assistant.tenant_id.is_(None))

        query = query.order_by(desc(Assistant.sort_order), desc(Assistant.created_at))
        result = await self.session.execute(query)

        assistants = list(result.scalars().all())
        return self._format_assistants(assistants)

    async def list_all_cursor(
        self,
        cursor: Optional[str] = None,
        limit: int = 10,
        category_id: Optional[str] = None,
        search: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """List assistants with cursor-based pagination

        Args:
            cursor: Cursor string (base64 encoded datetime or id)
            limit: Items per page
            category_id: Filter by category ID
            search: Search in name, profession, and description
            tenant_id: Optional tenant ID to filter by. If None, filters for assistants with no tenant_id

        Returns:
            Dictionary with assistants, next_cursor, and has_more
        """
        import base64
        import json
        import sqlalchemy

        query = select(Assistant)

        if category_id:
            try:
                cat_uuid = uuid.UUID(category_id)
                query = query.where(Assistant.category_id == cat_uuid)
            except ValueError:
                return {"assistants": [], "next_cursor": None, "has_more": False}

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (Assistant.name.ilike(search_pattern)) |
                (Assistant.profession.ilike(search_pattern)) |
                (Assistant.description.ilike(search_pattern))
            )

        if tenant_id is not None:
            query = query.where(Assistant.tenant_id == tenant_id)
        else:
            query = query.where(Assistant.tenant_id.is_(None))

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

        next_cursor = None
        if formatted_assistants:
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

    def _format_assistants(self, assistants: List[Assistant]) -> List[Assistant]:
        """Format assistant data, prepending CDN URL to avatar, prompt_file and source_url if they are just paths"""
        import copy

        formatted_assistants = []
        base_url = 'https://sudoclaw-1309794936.cos.ap-beijing.myqcloud.com'

        for assistant in assistants:
            # Clone to avoid modifying original SQLAlchemy object state
            ast_dict = {c.name: getattr(assistant, c.name) for c in assistant.__table__.columns}
            cloned = Assistant(**ast_dict)

            if cloned.avatar and not cloned.avatar.startswith('http'):
                cloned.avatar = f"{base_url}/{cloned.avatar}"

            if cloned.prompt_file and not cloned.prompt_file.startswith('http'):
                cloned.prompt_file = f"{base_url}/{cloned.prompt_file}"

            if cloned.source_url and not cloned.source_url.startswith('http'):
                cloned.source_url = f"{base_url}/{cloned.source_url}"

            formatted_assistants.append(cloned)

        return formatted_assistants
        
    async def create(self, data: Dict[str, Any]) -> Assistant:
        """Create a new assistant
        
        Args:
            data: Assistant data
            
        Returns:
            Created Assistant
        """
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

"""Category service"""

import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy import select, update, delete, asc
from sqlalchemy.ext.asyncio import AsyncSession

from skill_hub.models.category import Category

class CategoryService:
    """Service for managing categories"""
    
    def __init__(self, session: AsyncSession):
        """Initialize service with database session"""
        self.session = session
        
    async def get_by_id(self, category_id: str) -> Optional[Category]:
        """Get category by ID
        
        Args:
            category_id: Category UUID
            
        Returns:
            Category if found, None otherwise
        """
        try:
            # Parse UUID if it's a string
            if isinstance(category_id, str):
                category_uuid = uuid.UUID(category_id)
            else:
                category_uuid = category_id
                
            query = select(Category).where(Category.id == category_uuid)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except ValueError:
            # Invalid UUID string
            return None
            
    async def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name

        Args:
            name: Category name

        Returns:
            Category if found, None otherwise
        """
        query = select(Category).where(Category.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name_and_type(self, name: str, category_type: int) -> Optional[Category]:
        """Get category by name and type

        Args:
            name: Category name
            category_type: Category type (0=skill, 1=assistant)

        Returns:
            Category if found, None otherwise
        """
        query = select(Category).where(
            Category.name == name,
            Category.type == category_type
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_all(self, type_filter: Optional[int] = None) -> List[Category]:
        """Get all categories ordered by order_index

        Args:
            type_filter: Optional integer to filter by category type

        Returns:
            List of Category objects
        """
        query = select(Category)

        if type_filter is not None:
            query = query.where(Category.type == type_filter)

        query = query.order_by(asc(Category.order_index))
        result = await self.session.execute(query)
        return list(result.scalars().all())
        
    async def create(self, data: Dict[str, Any]) -> Category:
        """Create a new category
        
        Args:
            data: Category data
            
        Returns:
            Created Category
        """
        category = Category(**data)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
        
    async def update(self, category_id: str, data: Dict[str, Any]) -> Optional[Category]:
        """Update a category
        
        Args:
            category_id: Category UUID
            data: Data to update
            
        Returns:
            Updated Category if found, None otherwise
        """
        try:
            if isinstance(category_id, str):
                category_uuid = uuid.UUID(category_id)
            else:
                category_uuid = category_id
                
            # First check if exists
            category = await self.get_by_id(category_uuid)
            if not category:
                return None
                
            # Update fields
            for key, value in data.items():
                if hasattr(category, key):
                    setattr(category, key, value)
                    
            await self.session.commit()
            await self.session.refresh(category)
            return category
            
        except ValueError:
            return None
            
    async def delete(self, category_id: str) -> bool:
        """Delete a category
        
        Args:
            category_id: Category UUID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            if isinstance(category_id, str):
                category_uuid = uuid.UUID(category_id)
            else:
                category_uuid = category_id
                
            category = await self.get_by_id(category_uuid)
            if not category:
                return False
                
            await self.session.delete(category)
            await self.session.commit()
            return True
            
        except ValueError:
            return False

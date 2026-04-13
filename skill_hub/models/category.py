"""Category model definition"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from skill_hub.models.skill import Base


class Category(Base):
    """Category model representing a skill category.
    
    Attributes:
        id: Unique identifier for the category (UUID)
        name: Unique identifier/code (e.g., ai_vision)
        display_name: Display name (e.g., AI/Vision)
        order_index: Ordering index for display purposes
        created_at: Creation time
        updated_at: Last update time
    """
    
    __tablename__ = "categories"

    # Add composite unique constraint
    __table_args__ = (
        UniqueConstraint('name', 'type', name='uix_category_name_type'),
    )

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique identifier for the category"
    )
    
    # Category details
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Category code/identifier"
    )
    
    display_name = Column(
        String(255),
        nullable=False,
        comment="Display name"
    )
    
    order_index = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Ordering index for display"
    )
    
    icon_url = Column(
        String(200),
        nullable=True,
        comment="Icon URL for the category"
    )

    type = Column(
        Integer,
        default=0,
        nullable=False,
        comment="0 for skill, 1 for assistant"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="Creation time"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update time"
    )
    
    def __repr__(self) -> str:
        """String representation of the category"""
        return f"<Category(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"
    
    def to_dict(self) -> dict:
        """Convert category to dictionary representation"""
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "order_index": self.order_index,
            "icon_url": self.icon_url,
            "type": self.type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        """Create a Category instance from dictionary data"""
        category = cls()
        
        if "id" in data and data["id"]:
            category.id = uuid.UUID(data["id"]) if isinstance(data["id"], str) else data["id"]
            
        if "name" in data:
            category.name = data["name"]
            
        if "display_name" in data:
            category.display_name = data["display_name"]
            
        if "order_index" in data:
            category.order_index = data["order_index"]
            
        if "icon_url" in data:
            category.icon_url = data["icon_url"]

        if "type" in data:
            category.type = data["type"]

        if "created_at" in data and data["created_at"]:
            if isinstance(data["created_at"], str):
                category.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
            else:
                category.created_at = data["created_at"]
                
        if "updated_at" in data and data["updated_at"]:
            if isinstance(data["updated_at"], str):
                category.updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
            else:
                category.updated_at = data["updated_at"]
                
        return category

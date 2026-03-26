"""Skill model definition"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Skill(Base):
    """Skill model representing a skill in the system.
    
    Attributes:
        id: Unique identifier for the skill (UUID)
        name: Folder name/unique identifier (e.g., weather)
        display_name: Display name (e.g., Weather Forecast Expert)
        author_id: Developer ID (UUID)
        description: Description from SKILL.md, used for keyword search
        category: Category (e.g., AI/Vision, Tools, Social)
        emoji: Corresponding icon (from metadata)
        homepage: Skill homepage link
        star_count: Number of stars/likes
        created_at: First listing time
        updated_at: Last update time
    """
    
    __tablename__ = "skills"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique identifier for the skill"
    )
    
    # Skill identification
    name = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Folder name/unique identifier (e.g., weather)"
    )
    
    display_name = Column(
        String(255),
        nullable=False,
        comment="Display name (e.g., Weather Forecast Expert)"
    )
    
    # Author information
    author_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Developer ID"
    )
    
    # Skill details
    description = Column(
        Text,
        nullable=True,
        comment="Description from SKILL.md, used for keyword search"
    )
    
    core_features = Column(
        Text,
        nullable=True,
        comment="Core features of the skill"
    )
    
    applicable_scenarios = Column(
        Text,
        nullable=True,
        comment="Applicable scenarios for the skill"
    )
    
    category = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Category (e.g., AI/Vision, Tools, Social)"
    )
    
    categories = Column(
        ARRAY(String),
        nullable=True,
        comment="Array of category names or IDs"
    )
    
    emoji = Column(
        String(10),
        nullable=True,
        comment="Corresponding icon (from metadata)"
    )
    
    icon = Column(
        String(200),
        nullable=True,
        comment="Icon URL or path"
    )
    
    homepage = Column(
        String(500),
        nullable=True,
        comment="Skill homepage link"
    )
    
    # Statistics
    star_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of stars/likes"
    )
    
    status = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Skill status (0: default/active, other values for specific states)"
    )
    
    sort_order = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Sort order for display priority"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="First listing time"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update time"
    )
    
    def __repr__(self) -> str:
        """String representation of the skill"""
        return f"<Skill(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"
    
    # Relationships (use string reference to avoid circular import)
    versions = relationship("SkillVersion", back_populates="skill", cascade="all, delete-orphan")
    
    def to_dict(self) -> dict:
        """Convert skill to dictionary representation
        
        Returns:
            Dictionary containing skill data
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "author_id": str(self.author_id),
            "description": self.description,
            "category": self.category,
            "categories": self.categories,
            "emoji": self.emoji,
            "icon": self.icon,
            "homepage": self.homepage,
            "star_count": self.star_count,
            "status": self.status,
            "sort_order": self.sort_order,
            "core_features": self.core_features,
            "applicable_scenarios": self.applicable_scenarios,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Skill":
        """Create a Skill instance from dictionary data
        
        Args:
            data: Dictionary containing skill data
            
        Returns:
            Skill instance
        """
        skill = cls()
        
        # Set attributes from dictionary
        if "id" in data and data["id"]:
            skill.id = uuid.UUID(data["id"]) if isinstance(data["id"], str) else data["id"]
        
        if "name" in data:
            skill.name = data["name"]
        
        if "display_name" in data:
            skill.display_name = data["display_name"]
        
        if "author_id" in data and data["author_id"]:
            skill.author_id = uuid.UUID(data["author_id"]) if isinstance(data["author_id"], str) else data["author_id"]
        
        if "description" in data:
            skill.description = data["description"]
            
        if "core_features" in data:
            skill.core_features = data["core_features"]
            
        if "applicable_scenarios" in data:
            skill.applicable_scenarios = data["applicable_scenarios"]
        
        if "category" in data:
            skill.category = data["category"]

        if "categories" in data:
            skill.categories = data["categories"]
        
        if "emoji" in data:
            skill.emoji = data["emoji"]
            
        if "icon" in data:
            skill.icon = data["icon"]
        
        if "homepage" in data:
            skill.homepage = data["homepage"]
        
        if "star_count" in data:
            skill.star_count = data["star_count"]
            
        if "status" in data:
            skill.status = data["status"]
            
        if "sort_order" in data:
            skill.sort_order = data["sort_order"]
        
        # Handle timestamps
        if "created_at" in data and data["created_at"]:
            if isinstance(data["created_at"], str):
                skill.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
            else:
                skill.created_at = data["created_at"]
        
        if "updated_at" in data and data["updated_at"]:
            if isinstance(data["updated_at"], str):
                skill.updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
            else:
                skill.updated_at = data["updated_at"]
        
        return skill

"""Assistant model definition"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from skill_hub.models.skill import Base

class Assistant(Base):
    """Assistant model representing a digital assistant.
    
    Attributes:
        id: Unique identifier
        name: Name of the assistant
        profession: Role/profession
        description: Description of capabilities
        prompt_file: Path/URL to the prompt md file
        avatar: URL to the avatar
        default_init_prompt: Default initial prompt text
        category_id: Reference to the category
        created_at: Creation time
        updated_at: Last update time
    """
    
    __tablename__ = "assistants"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique identifier for the assistant"
    )
    
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Assistant name"
    )
    
    profession = Column(
        String(255),
        nullable=False,
        comment="Assistant profession/role"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Assistant description"
    )
    
    prompt_file = Column(
        String(500),
        nullable=True,
        comment="Path or URL to the markdown prompt file"
    )
    
    avatar = Column(
        String(500),
        nullable=True,
        comment="URL to the assistant avatar image"
    )
    
    default_init_prompt = Column(
        Text,
        nullable=True,
        comment="Default initial prompt text"
    )
    
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference to the category (must be type 1)"
    )
    
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
        return f"<Assistant(id={self.id}, name='{self.name}', profession='{self.profession}')>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation, exposing camelCase keys for API."""
        return {
            "id": str(self.id),
            "name": self.name,
            "profession": self.profession,
            "description": self.description,
            "promptFile": self.prompt_file,
            "avatar": self.avatar,
            "defaultInitPrompt": self.default_init_prompt,
            "categoryId": str(self.category_id) if self.category_id else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Assistant":
        """Create an Assistant instance from dictionary data."""
        assistant = cls()
        
        if "id" in data and data["id"]:
            assistant.id = uuid.UUID(data["id"]) if isinstance(data["id"], str) else data["id"]
            
        if "name" in data:
            assistant.name = data["name"]
            
        if "profession" in data:
            assistant.profession = data["profession"]
            
        if "description" in data:
            assistant.description = data["description"]
            
        if "promptFile" in data:
            assistant.prompt_file = data["promptFile"]
        elif "prompt_file" in data:
            assistant.prompt_file = data["prompt_file"]
            
        if "avatar" in data:
            assistant.avatar = data["avatar"]
            
        if "defaultInitPrompt" in data:
            assistant.default_init_prompt = data["defaultInitPrompt"]
        elif "default_init_prompt" in data:
            assistant.default_init_prompt = data["default_init_prompt"]
            
        if "categoryId" in data and data["categoryId"]:
            assistant.category_id = uuid.UUID(data["categoryId"]) if isinstance(data["categoryId"], str) else data["categoryId"]
        elif "category_id" in data and data["category_id"]:
            assistant.category_id = uuid.UUID(data["category_id"]) if isinstance(data["category_id"], str) else data["category_id"]
            
        if "createdAt" in data and data["createdAt"]:
            if isinstance(data["createdAt"], str):
                assistant.created_at = datetime.fromisoformat(data["createdAt"].replace('Z', '+00:00'))
            else:
                assistant.created_at = data["createdAt"]
                
        if "updatedAt" in data and data["updatedAt"]:
            if isinstance(data["updatedAt"], str):
                assistant.updated_at = datetime.fromisoformat(data["updatedAt"].replace('Z', '+00:00'))
            else:
                assistant.updated_at = data["updatedAt"]
                
        return assistant

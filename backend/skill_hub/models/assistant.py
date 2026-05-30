"""Assistant model definition"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY

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
        tenant_id: Tenant ID
        sort_order: Sort order for display priority
        categories: Array of category names or IDs
        skills: Array of associated skill IDs
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

    source_url = Column(
        String(500),
        nullable=True,
        comment="URL to the uploaded zip file"
    )

    default_init_prompt = Column(
        Text,
        nullable=True,
        comment="Default initial prompt text"
    )

    tenant_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Tenant ID"
    )

    sort_order = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Sort order for display priority"
    )

    categories = Column(
        ARRAY(String),
        nullable=True,
        comment="Array of category names or IDs"
    )

    status = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Assistant status (0: pending review, 1: active/approved, other values for specific states)"
    )

    skills = Column(
        ARRAY(UUID(as_uuid=True)),
        nullable=True,
        comment="Array of associated skill IDs"
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
            "sourceUrl": self.source_url,
            "defaultInitPrompt": self.default_init_prompt,
            "tenantId": self.tenant_id,
            "sortOrder": self.sort_order,
            "categories": self.categories,
            "status": self.status,
            "skills": [str(s) for s in self.skills] if self.skills else [],
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

        if "sourceUrl" in data:
            assistant.source_url = data["sourceUrl"]
        elif "source_url" in data:
            assistant.source_url = data["source_url"]

        if "defaultInitPrompt" in data:
            assistant.default_init_prompt = data["defaultInitPrompt"]
        elif "default_init_prompt" in data:
            assistant.default_init_prompt = data["default_init_prompt"]

        if "tenantId" in data:
            assistant.tenant_id = data["tenantId"]
        elif "tenant_id" in data:
            assistant.tenant_id = data["tenant_id"]

        if "sortOrder" in data:
            assistant.sort_order = data["sortOrder"]
        if "sort_order" in data:
            assistant.sort_order = data["sort_order"]

        if "status" in data:
            assistant.status = data["status"]

        if "categories" in data:
            assistant.categories = data["categories"]

        if "skills" in data:
            assistant.skills = [uuid.UUID(s) if isinstance(s, str) else s for s in data["skills"]]

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

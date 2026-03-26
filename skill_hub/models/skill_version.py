"""Skill Version model"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from skill_hub.models.skill import Base


class SkillVersion(Base):
    """Skill Version model representing different versions of a skill
    
    Attributes:
        id: Unique identifier for the version
        skill_id: Foreign key referencing the parent skill
        version: Semantic version (e.g., v1.2.0)
        source_url: URL to download the compressed package or Git repository
        checksum: SHA-256 hash of the file for security verification
        changelog: Description of changes in this version
        readme_content: Full content of SKILL.md for display in details
        created_at: Timestamp when the version was created
        updated_at: Timestamp when the version was last updated
    """
    
    __tablename__ = "skill_versions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to skills table
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    
    # Version information
    version = Column(String(50), nullable=False)
    source_url = Column(Text, nullable=False)
    checksum = Column(String(64), nullable=False)  # SHA-256 hash (64 characters)
    changelog = Column(Text)
    readme_content = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship (use string reference to avoid circular import)
    skill = relationship("Skill", back_populates="versions")
    
    def __init__(
        self,
        skill_id: uuid.UUID,
        version: str,
        source_url: str,
        checksum: str,
        changelog: Optional[str] = None,
        readme_content: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        """Initialize a new SkillVersion instance
        
        Args:
            skill_id: Foreign key referencing the parent skill
            version: Semantic version (e.g., v1.2.0)
            source_url: URL to download the compressed package or Git repository
            checksum: SHA-256 hash of the file for security verification
            changelog: Description of changes in this version
            readme_content: Full content of SKILL.md for display in details
            created_at: Timestamp when the version was created
            updated_at: Timestamp when the version was last updated
        """
        self.skill_id = skill_id
        self.version = version
        self.source_url = source_url
        self.checksum = checksum
        self.changelog = changelog
        self.readme_content = readme_content
        
        if created_at:
            self.created_at = created_at if isinstance(created_at, datetime) else datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
        if updated_at:
            self.updated_at = updated_at if isinstance(updated_at, datetime) else datetime.fromisoformat(str(updated_at).replace('Z', '+00:00'))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the skill version to a dictionary
        
        Returns:
            Dictionary representation of the skill version
        """
        return {
            "id": str(self.id),
            "skill_id": str(self.skill_id),
            "version": self.version,
            "source_url": "https://sudoclaw-1309794936.cos.ap-beijing.myqcloud.com/" + self.source_url,
            "checksum": self.checksum,
            "changelog": self.changelog,
            "readme_content": self.readme_content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillVersion":
        """Create a SkillVersion instance from a dictionary
        
        Args:
            data: Dictionary containing skill version data
            
        Returns:
            SkillVersion instance
        """
        # Parse UUIDs
        skill_id = uuid.UUID(data["skill_id"]) if "skill_id" in data else None
        
        # Parse datetimes
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        
        # Create instance
        instance = cls(
            skill_id=skill_id,
            version=data.get("version", ""),
            source_url=data.get("source_url", ""),
            checksum=data.get("checksum", ""),
            changelog=data.get("changelog"),
            readme_content=data.get("readme_content"),
            created_at=created_at,
            updated_at=updated_at,
        )
        
        # Set ID if provided
        if "id" in data and data["id"]:
            instance.id = uuid.UUID(data["id"])
        
        return instance
    
    def __repr__(self) -> str:
        """String representation of the skill version
        
        Returns:
            String representation
        """
        return f"<SkillVersion(id={self.id}, skill_id={self.skill_id}, version={self.version})>"
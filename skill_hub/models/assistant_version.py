"""Assistant Version model"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from skill_hub.models.skill import Base


class AssistantVersion(Base):
    """Version metadata for assistant source packages."""

    __tablename__ = "assistant_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assistant_id = Column(UUID(as_uuid=True), ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(50), nullable=False)
    source_url = Column(Text, nullable=False)
    checksum = Column(String(64), nullable=False)
    changelog = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    assistant = relationship("Assistant", back_populates="versions")

    def __init__(
        self,
        assistant_id: uuid.UUID,
        version: str,
        source_url: str,
        checksum: str,
        changelog: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        self.assistant_id = assistant_id
        self.version = version
        self.source_url = source_url
        self.checksum = checksum
        self.changelog = changelog

        if created_at:
            self.created_at = created_at if isinstance(created_at, datetime) else datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        if updated_at:
            self.updated_at = updated_at if isinstance(updated_at, datetime) else datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))

    def to_dict(self) -> Dict[str, Any]:
        from skill_hub.utils.content_storage import cos_base_url, is_local_mode, resolve_local_only

        def _resolve(value):
            if not value or value.startswith(("http://", "https://")):
                return value
            if is_local_mode():
                return resolve_local_only(value)
            return f"{cos_base_url()}/{value}"

        return {
            "id": str(self.id),
            "assistant_id": str(self.assistant_id),
            "version": self.version,
            "source_url": _resolve(self.source_url),
            "checksum": self.checksum,
            "changelog": self.changelog,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssistantVersion":
        assistant_id = uuid.UUID(data["assistant_id"]) if "assistant_id" in data else None

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        instance = cls(
            assistant_id=assistant_id,
            version=data.get("version", ""),
            source_url=data.get("source_url", ""),
            checksum=data.get("checksum", ""),
            changelog=data.get("changelog"),
            created_at=created_at,
            updated_at=updated_at,
        )

        if "id" in data and data["id"]:
            instance.id = uuid.UUID(data["id"])

        return instance

    def __repr__(self) -> str:
        return f"<AssistantVersion(id={self.id}, assistant_id={self.assistant_id}, version={self.version})>"

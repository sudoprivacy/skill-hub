"""Role model definition"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID

# Share the single declarative Base used across all models.
from skill_hub.models.skill import Base

# Canonical role names
ROLE_ADMIN = "admin"
ROLE_USER = "user"


class Role(Base):
    """Role for access control. Seeded with `admin` and `user`."""

    __tablename__ = "roles"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique identifier for the role",
    )

    name = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="Role name (admin / user)",
    )

    description = Column(
        String(255),
        nullable=True,
        comment="Human-readable description",
    )

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
        }

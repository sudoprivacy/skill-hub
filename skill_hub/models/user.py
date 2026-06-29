"""User model definition"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Share the single declarative Base used across all models.
from skill_hub.models.skill import Base


class User(Base):
    """Application user authenticated via username + password."""

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique identifier for the user",
    )

    username = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Login name (unique)",
    )

    password_hash = Column(
        String(255),
        nullable=False,
        comment="Hashed password (werkzeug)",
    )

    display_name = Column(
        String(100),
        nullable=True,
        comment="Optional display name",
    )

    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id"),
        nullable=False,
        index=True,
        comment="Role reference",
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the account can log in",
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

    # Eager-load role so to_dict can expose the role name without extra queries.
    role = relationship("Role", lazy="selectin")

    def to_dict(self) -> dict:
        """Serialize the user WITHOUT the password hash."""
        return {
            "id": str(self.id),
            "username": self.username,
            "display_name": self.display_name,
            "role": self.role.name if self.role else None,
            "role_id": str(self.role_id) if self.role_id else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

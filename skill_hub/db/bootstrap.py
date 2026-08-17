"""Idempotent startup bootstrap for the auth schema.

Because this project has no automated migration runner (deploy just runs the
app), we ensure the auth-related schema and seed data exist on startup:

1. Create the ``roles`` and ``users`` tables if missing.
2. Add the nullable ``creator_id`` column to ``skills`` / ``assistants``.
3. Seed the ``admin`` / ``user`` roles.
4. Create the bootstrap admin user from configuration (if absent).

Every step is idempotent and additive — existing data is never modified.
A matching SQL migration is also provided under ``migrations/`` for the record.
"""

import logging

from sqlalchemy import select, text
from werkzeug.security import generate_password_hash

from skill_hub.config.config import Config
from skill_hub.db.database import get_engine, get_session
from skill_hub.models.skill import Base
from skill_hub.models.role import Role, ROLE_ADMIN, ROLE_USER
from skill_hub.models.user import User

logger = logging.getLogger(__name__)


async def bootstrap_auth(config: Config) -> None:
    """Ensure auth tables, columns, roles and the bootstrap admin exist."""
    try:
        await _ensure_tables_and_columns()
        await _seed_roles_and_admin(config)
        logger.info("Auth bootstrap completed")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Auth bootstrap failed: %s", exc)
        raise


async def _ensure_tables_and_columns() -> None:
    """Create roles/users tables and add creator_id columns (idempotent)."""
    engine = get_engine()
    async with engine.begin() as conn:
        # Create only the two new tables; existing tables are left untouched.
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[Role.__table__, User.__table__],
        )
        # Add ownership columns. Postgres supports IF NOT EXISTS, so this is
        # safe to run on every boot.
        await conn.execute(
            text(
                "ALTER TABLE skills ADD COLUMN IF NOT EXISTS "
                "creator_id UUID REFERENCES users(id)"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE assistants ADD COLUMN IF NOT EXISTS "
                "creator_id UUID REFERENCES users(id)"
            )
        )


async def _seed_roles_and_admin(config: Config) -> None:
    """Seed admin/user roles and the bootstrap admin account."""
    async with get_session() as session:
        # Seed roles
        role_ids: dict[str, object] = {}
        for name, desc in [
            (ROLE_ADMIN, "Administrator with full access"),
            (ROLE_USER, "Regular user"),
        ]:
            existing = await session.execute(
                select(Role).where(Role.name == name)
            )
            role = existing.scalar_one_or_none()
            if role is None:
                role = Role(name=name, description=desc)
                session.add(role)
                await session.flush()
                logger.info("Seeded role: %s", name)
            role_ids[name] = role.id

        # Ensure bootstrap admin (only when a password is configured)
        if not config.admin_password:
            logger.warning(
                "SKILL_HUB_ADMIN_PASSWORD not set; skipping admin bootstrap"
            )
            await session.commit()
            return

        existing_admin = await session.execute(
            select(User).where(User.username == config.admin_username)
        )
        if existing_admin.scalar_one_or_none() is None:
            admin = User(
                username=config.admin_username,
                password_hash=generate_password_hash(config.admin_password),
                display_name="Administrator",
                role_id=role_ids[ROLE_ADMIN],
                is_active=True,
            )
            session.add(admin)
            logger.info("Created bootstrap admin user: %s", config.admin_username)

        await session.commit()

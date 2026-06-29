"""User & role service."""

import uuid
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.security import generate_password_hash, check_password_hash

from skill_hub.models.user import User
from skill_hub.models.role import Role, ROLE_USER


class UserService:
    """CRUD + authentication for application users."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ---- roles -------------------------------------------------------------
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        result = await self.session.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def list_roles(self) -> List[Role]:
        result = await self.session.execute(select(Role).order_by(Role.name))
        return list(result.scalars().all())

    # ---- queries -----------------------------------------------------------
    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            return None
        result = await self.session.execute(select(User).where(User.id == uid))
        return result.scalar_one_or_none()

    async def list_users(self) -> List[User]:
        result = await self.session.execute(
            select(User).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())

    # ---- auth --------------------------------------------------------------
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        user = await self.get_by_username(username)
        if not user or not user.is_active:
            return None
        if not check_password_hash(user.password_hash, password):
            return None
        return user

    # ---- mutations ---------------------------------------------------------
    async def create(
        self,
        username: str,
        password: str,
        role_name: str = ROLE_USER,
        display_name: Optional[str] = None,
    ) -> User:
        role = await self.get_role_by_name(role_name) or await self.get_role_by_name(
            ROLE_USER
        )
        user = User(
            username=username.strip(),
            password_hash=generate_password_hash(password),
            display_name=display_name,
            role_id=role.id,
            is_active=True,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(
        self,
        user_id: str,
        *,
        password: Optional[str] = None,
        role_name: Optional[str] = None,
        display_name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None

        if password:
            user.password_hash = generate_password_hash(password)
        if role_name:
            role = await self.get_role_by_name(role_name)
            if role:
                user.role_id = role.id
        if display_name is not None:
            user.display_name = display_name
        if is_active is not None:
            user.is_active = is_active

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user_id: str) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        await self.session.delete(user)
        await self.session.commit()
        return True

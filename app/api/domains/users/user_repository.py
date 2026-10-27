from uuid import UUID

from sqlalchemy import asc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.base_repository import BaseRepository
from app.api.domains.users.services.security import Security
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.users import UserRoleTable, UsersTable


class UserRepository(BaseRepository):
    def __init__(self, security: Security):
        self._security: Security = security

    async def get_by_uuid(self, session: AsyncSession, uuid: UUID) -> UsersTable | None:
        stmt = select(UsersTable).options(selectinload(UsersTable.user_roles)).where(UsersTable.id == uuid)
        return await self.fetch_first(session, stmt)

    async def get_by_email(self, session: AsyncSession, email: str) -> UsersTable | None:
        stmt = select(UsersTable).options(selectinload(UsersTable.user_roles)).where(UsersTable.email == email)
        return await self.fetch_first(session, stmt)

    async def get_filtered(
        self,
        session: AsyncSession,
        pagination: SortedPagination,
        role: str | None,
        query: str | None,
        active: bool | None,
    ) -> PaginatedQueryResult:
        stmt = select(UsersTable).options(selectinload(UsersTable.user_roles))

        if role is not None:
            stmt = stmt.filter(UsersTable.user_roles.any(UserRoleTable.role == role))

        if query is not None:
            stmt = stmt.filter(or_(UsersTable.name.like(f"%{query}%"), UsersTable.email.like(f"%{query}%")))

        if active is not None:
            if active:
                stmt = stmt.filter(UsersTable.is_active == True)
            else:
                stmt = stmt.filter(UsersTable.is_active != True)

        return await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(UsersTable, pagination.sort.column), pagination.sort.order),
        )

    async def get_active(self, session: AsyncSession, pagination: SortedPagination) -> PaginatedQueryResult:
        stmt = select(UsersTable).options(selectinload(UsersTable.user_roles)).filter(UsersTable.is_active == True)
        return await self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(UsersTable, pagination.sort.column), pagination.sort.order),
        )

    async def get_all(self, session: AsyncSession) -> list[UsersTable]:
        stmt = select(UsersTable).options(selectinload(UsersTable.user_roles)).order_by(asc(UsersTable.name))
        return await self.fetch_all(session, stmt)

    async def authenticate(self, session: AsyncSession, username: str, password: str) -> UsersTable | None:
        if not username:
            return None

        stmt = (
            select(UsersTable)
            .options(selectinload(UsersTable.user_roles))
            .filter(UsersTable.email == username)
            .filter(UsersTable.is_active == True)
        )
        maybe_user: UsersTable | None = await self.fetch_first(session, stmt)

        if not maybe_user:
            return None
        if not (await self._security.verify_password(password, maybe_user.password_hashed)):
            return None
        return maybe_user

    async def change_password(self, session: AsyncSession, user: UsersTable, new_password: str):
        new_hash = await self._security.get_password_hash(new_password)
        user.password_hashed = new_hash
        session.add(user)
        await session.flush()
        await session.commit()

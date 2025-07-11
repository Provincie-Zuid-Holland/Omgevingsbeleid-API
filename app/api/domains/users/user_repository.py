from typing import List, Optional
from uuid import UUID

from sqlalchemy import asc, or_, select
from sqlalchemy.orm import Session

from app.api.base_repository import BaseRepository
from app.api.domains.users.services.security import Security
from app.api.utils.pagination import PaginatedQueryResult, SortedPagination
from app.core.tables.users import IS_ACTIVE, UsersTable


class UserRepository(BaseRepository):
    def __init__(self, security: Security):
        self._security: Security = security

    def get_by_uuid(self, session: Session, uuid: UUID) -> Optional[UsersTable]:
        stmt = select(UsersTable).where(UsersTable.UUID == uuid)
        return self.fetch_first(session, stmt)

    def get_by_email(self, session: Session, email: str) -> Optional[UsersTable]:
        stmt = select(UsersTable).where(UsersTable.Email == email)
        return self.fetch_first(session, stmt)

    def get_filtered(
        self,
        session: Session,
        pagination: SortedPagination,
        role: Optional[str],
        query: Optional[str],
        active: Optional[bool],
    ) -> PaginatedQueryResult:
        stmt = select(UsersTable)

        if role is not None:
            stmt = stmt.filter(UsersTable.Rol == role)

        if query is not None:
            stmt = stmt.filter(or_(UsersTable.Gebruikersnaam.like(f"%{query}%"), UsersTable.Email.like(f"%{query}%")))

        if active is not None:
            if active:
                stmt = stmt.filter(UsersTable.Status == IS_ACTIVE)
            else:
                stmt = stmt.filter(UsersTable.Status != IS_ACTIVE)

        return self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(UsersTable, pagination.sort.column), pagination.sort.order),
        )

    def get_active(self, session: Session, pagination: SortedPagination) -> PaginatedQueryResult:
        stmt = select(UsersTable).filter(UsersTable.Status == IS_ACTIVE)
        return self.fetch_paginated(
            session=session,
            statement=stmt,
            offset=pagination.offset,
            limit=pagination.limit,
            sort=(getattr(UsersTable, pagination.sort.column), pagination.sort.order),
        )

    def get_all(self, session: Session) -> List[UsersTable]:
        stmt = select(UsersTable).order_by(asc(UsersTable.Gebruikersnaam))
        return self.fetch_all(session, stmt)

    def authenticate(self, session: Session, username: str, password: str) -> Optional[UsersTable]:
        if not username:
            return None

        stmt = select(UsersTable).filter(UsersTable.Email == username).filter(UsersTable.Status == IS_ACTIVE)
        maybe_user: Optional[UsersTable] = self.fetch_first(session, stmt)

        if not maybe_user:
            return None
        if not self._security.verify_password(password, maybe_user.Wachtwoord):
            return None
        return maybe_user

    def change_password(self, session: Session, user: UsersTable, new_password: str):
        new_hash = self._security.get_password_hash(new_password)
        user.Wachtwoord = new_hash
        session.add(user)
        session.flush()
        session.commit()

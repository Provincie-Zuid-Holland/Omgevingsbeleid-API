from typing import List, Optional
from uuid import UUID

from sqlalchemy import asc, select

from app.core.security import get_password_hash, verify_password
from app.dynamic.repository import BaseRepository
from app.dynamic.utils.pagination import PaginatedQueryResult
from app.extensions.users.db.tables import UsersTable

from ..model import User


class UserRepository(BaseRepository):
    def get_by_uuid(self, uuid: UUID) -> Optional[UsersTable]:
        stmt = select(UsersTable).where(UsersTable.UUID == uuid)
        return self.fetch_first(stmt)

    def get_active(self, limit: int = 20, offset: int = 0) -> PaginatedQueryResult:
        stmt = select(UsersTable).filter(UsersTable.Status == "Actief").order_by(asc(UsersTable.Gebruikersnaam))
        return self.fetch_paginated(stmt, limit, offset)

    def get_all(self) -> List[UsersTable]:
        stmt = select(UsersTable).order_by(asc(UsersTable.Gebruikersnaam))
        return self.fetch_all(stmt)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        stmt = select(UsersTable).where(UsersTable.Email == username)
        maybe_user: Optional[UsersTable] = self.fetch_first(stmt)
        if not maybe_user:
            return None
        if not verify_password(password, maybe_user.Wachtwoord):
            return None
        return maybe_user

    def change_password(self, user: UsersTable, new_password: str):
        new_hash = get_password_hash(new_password)
        user.Wachtwoord = new_hash
        self._db.add(user)
        self._db.flush()
        self._db.commit()

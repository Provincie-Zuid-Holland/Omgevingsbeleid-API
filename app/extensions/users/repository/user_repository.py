from typing import List, Optional
from uuid import UUID
from sqlalchemy import asc, select

from sqlalchemy.orm import Session

from app.core.security import verify_password, get_password_hash
from app.extensions.users.db.tables import UsersTable
from ..model import User


class UserRepository:
    def __init__(self, db: Session):
        self._db: Session = db

    def get_by_uuid(self, uuid: UUID) -> Optional[UsersTable]:
        stmt = select(UsersTable).where(UsersTable.UUID == uuid)
        maybe_user = self._db.scalars(stmt).first()
        return maybe_user

    def get_active(self) -> List[UsersTable]:
        stmt = (
            select(UsersTable)
            .filter(UsersTable.Status == "Actief")
            .order_by(asc(UsersTable.Gebruikersnaam))
        )
        users = self._db.scalars(stmt).all()
        return users

    def get_all(self) -> List[UsersTable]:
        stmt = select(UsersTable).order_by(asc(UsersTable.Gebruikersnaam))
        users = self._db.scalars(stmt).all()
        return users

    def authenticate(self, username: str, password: str) -> Optional[User]:
        stmt = select(UsersTable).where(UsersTable.Email == username)
        maybe_user: Optional[UsersTable] = self._db.scalars(stmt).first()
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

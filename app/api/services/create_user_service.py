import uuid

import validators
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.users.services.security import Security
from app.api.domains.users.user_repository import UserRepository
from app.core.tables.users import UsersTable


class CreateUserService:
    def __init__(self, repository: UserRepository, security: Security):
        self._repository: UserRepository = repository
        self._security: Security = security

    async def create_user(
        self,
        session: AsyncSession,
        name: str,
        email: str,
        password: str,
        roles: set[str],
        allowed_roles: set[str],
    ) -> UsersTable:
        if len(name) < 3:
            raise ValueError("Name is too short")
        if len(password) < 8:
            raise ValueError("Password is too short")
        if not roles:
            raise ValueError("At least one role is required")
        if not roles <= allowed_roles:
            raise ValueError("Invalid Roles")

        email = self._sanitize_email(email)
        if not validators.email(email):
            raise ValueError("Invalid email")

        password_hashed = await self._security.get_password_hash(password)

        email_exists: bool = await self._repository.email_exists(session, email)
        if email_exists:
            raise ValueError("Email already in use")

        user = UsersTable(
            id=uuid.uuid4(),
            name=name,
            email=email,
            roles=roles,
            is_active=True,
            password_hashed=password_hashed,
        )

        session.add(user)
        return user

    def _sanitize_email(self, email: str) -> str:
        return email.strip().lower()

    def generate_password(self) -> str:
        password: str = "change-me-" + self._security.get_random_password()
        return password

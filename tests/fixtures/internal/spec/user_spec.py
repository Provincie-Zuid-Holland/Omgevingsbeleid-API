import uuid
from collections.abc import Sequence

from passlib.context import CryptContext

from app.core.db.base import Base
from app.core.tables.users import UsersTable
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import UUID_NAMESPACE, BasePersistHandler, PersistContext, PrimaryKey, Record, Spec

DEFAULT_PASSWORD = "password"
IS_DISABLED = ""


class UserSpec(Spec):
    id: uuid.UUID | None = None
    name: str
    email: str
    roles: list[str]
    is_active: bool = True
    password: str = DEFAULT_PASSWORD
    password_hashed: str = ""

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.id, "id is not set which is expected to happen at this stage."
        return self.id


class UserPrefillHandler(BasePrefillHandler[UserSpec]):
    def __init__(self):
        self._pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def fill(self, record: Record[UserSpec], context: PrefillContext) -> Record[UserSpec]:
        record = super().fill(record, context)

        if record.spec.id is None:
            record.spec.id = uuid.uuid5(UUID_NAMESPACE, record.spec.email)

        record.spec.password_hashed = self._pwd_context.hash(record.spec.password)

        return record


class UserPersistHandler(BasePersistHandler[UserSpec]):
    def to_rows(self, record: Record[UserSpec], context: PersistContext) -> Sequence[Base]:
        spec: UserSpec = record.spec
        return [
            UsersTable(
                id=spec.id,
                name=spec.name,
                email=spec.email,
                roles=spec.roles,
                is_active=spec.is_active,
                password_hashed=spec.password_hashed,
            )
        ]



from typing import Optional
import uuid

from passlib.context import CryptContext
from pydantic import Field

from app.core.tables.users import IS_ACTIVE
from tests.fixtures.internal.services.base_handler import BasePrefillHandler, PrefillContext
from tests.fixtures.internal.types import Spec, Record, UUID_NAMESPACE, PrimaryKey


DEFAULT_PASSWORD = "password"
IS_DISABLED = ""


class UserSpec(Spec):
    UUID: Optional[uuid.UUID] = None
    Gebruikersnaam: str
    Email: str
    Rol: str
    Status: str = Field(default=IS_ACTIVE)
    Wachtwoord: str = Field(default=DEFAULT_PASSWORD)
    Wachtwoord_Hash: str = Field(default="")

    def get_table_primary_key(self) -> PrimaryKey:
        assert self.UUID, "UUID is not set which is expected to happen at this stage."
        return self.UUID


class UserPrefillHandler(BasePrefillHandler[UserSpec]):
    def __init__(self):
        self._pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def fill(self, record: Record[UserSpec], context: PrefillContext) -> Record[UserSpec]:
        record = super().fill(record, context)

        if record.spec.UUID is None:
            record.spec.UUID = uuid.uuid5(UUID_NAMESPACE, record.spec.Email)
        
        record.spec.Wachtwoord_Hash = self._pwd_context.hash(record.spec.Wachtwoord)

        return record

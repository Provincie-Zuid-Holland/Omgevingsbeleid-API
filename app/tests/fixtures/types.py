import hashlib
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel

from app.api.domains.users import Security
from app.core.tables.others import StorageFileTable
from app.core.tables.users import UsersTable


class FixtureContext:
    def __init__(self, security: Security):
        self._security = security

    @property
    def security(self):
        return self._security


class TypeEnum(Enum):
    USER = 1
    STORAGE_FILE = 2


class Factory(ABC, BaseModel):
    @abstractmethod
    def create(self) -> Any:
        pass

    @staticmethod
    def get_uuid_from_id(the_type: TypeEnum, the_id: int) -> uuid.UUID:
        return uuid.UUID(f"00000000-0000-0000-{str(the_type.value).zfill(4)}-{str(the_id).zfill(12)}")


class UserFactory(Factory):
    id: int
    rol: str
    wachtwoord: str
    status: str = "Actief"

    def create(self) -> UsersTable:
        name = self.rol.lower().replace(" ", "-")
        return UsersTable(
            UUID=self.get_uuid_from_id(TypeEnum.USER, self.id),
            Gebruikersnaam=name,
            Email=f"{name}@example.com",
            Rol=self.rol,
            Status=self.status,
            Wachtwoord=self.wachtwoord,
        )


class StorageFileFactory(Factory):
    id: int
    file_path: str
    created_date: datetime
    content_type: str = "application/pdf"

    def create(self) -> StorageFileTable:
        with open(self.file_path, "rb") as file:
            file_binary = file.read()
            file_size = len(file_binary)
            checksum = hashlib.sha256(file_binary).hexdigest()
            lookup = checksum[0:10]
            return StorageFileTable(
                UUID=self.get_uuid_from_id(TypeEnum.STORAGE_FILE, self.id),
                Checksum=checksum,
                Lookup=lookup,
                Filename=os.path.basename(self.file_path),
                Content_Type=self.content_type,
                Size=file_size,
                Binary=file_binary,
                Created_Date=self.created_date,
                Created_By_UUID=self.get_uuid_from_id(TypeEnum.USER, 1),
            )

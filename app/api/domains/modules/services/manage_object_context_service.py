
from datetime import datetime
import uuid
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from enum import Enum
from app.api.domains.modules.repositories.module_object_context_repository import ModuleObjectContextRepository
from app.core.tables.modules import ModuleObjectContextTable


class Request(BaseModel):
    module_id: int
    object_type: str
    object_id: int
    timepoint: datetime
    is_terminate: bool
    original_adjust_on: uuid.UUID
    explanation: str = Field("")
    conclusion: str = Field("")
    user_uuid:  uuid.UUID

    def get_code(self) -> str:
        return f"{self.object_type}-{self.object_id}"


class ResultType(str, Enum):
    CREATED = "CREATED"
    ACTIVATED = "ACTIVATED"
    ALREADY_EXIST = "ALREADY_EXIST"


class Result(BaseModel):
    object_context: ModuleObjectContextTable
    result_type: ResultType


class ManageObjectContextService:
    def __init__(self, context_repository: ModuleObjectContextRepository):
        self._context_repository: ModuleObjectContextRepository = context_repository

    def ensure_exists(
        self,
        session: Session,
    ) -> Result:
        ...

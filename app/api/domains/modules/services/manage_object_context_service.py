import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.domains.modules.repositories.module_object_context_repository import ModuleObjectContextRepository
from app.api.domains.modules.types import ModuleObjectActionFull
from app.core.tables.modules import ModuleObjectContextTable


class ExistRequest(BaseModel):
    module_id: int
    object_type: str
    object_id: int
    timepoint: datetime
    original_adjust_on: uuid.UUID | None
    explanation: str = Field("")
    conclusion: str = Field("")
    user_uuid: uuid.UUID

    def get_code(self) -> str:
        return f"{self.object_type}-{self.object_id}"


class ResultType(str, Enum):
    CREATED = "CREATED"
    ACTIVATED = "ACTIVATED"
    ALREADY_EXIST = "ALREADY_EXIST"


class Result(BaseModel):
    object_context: ModuleObjectContextTable
    result_type: ResultType

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ManageObjectContextService:
    def __init__(self, module_object_context_repository: ModuleObjectContextRepository):
        self._context_repository: ModuleObjectContextRepository = module_object_context_repository

    def ensure_exists(
        self,
        session: Session,
        request: ExistRequest,
    ) -> Result:
        existing_object_context: ModuleObjectContextTable | None = self._context_repository.get_by_ids(
            session,
            request.module_id,
            request.object_type,
            request.object_id,
        )

        # It could be that the object context exists but is hidden
        # This means that the object previously lived in the module but was removed
        # In that case we must activate the object context again
        match existing_object_context:
            case None:
                # Create
                object_context: ModuleObjectContextTable = ModuleObjectContextTable(
                    module_id=request.module_id,
                    object_type=request.object_type,
                    object_id=request.object_id,
                    code=request.get_code(),
                    created_date=request.timepoint,
                    modified_date=request.timepoint,
                    created_by_id=request.user_uuid,
                    modified_by_id=request.user_uuid,
                    original_adjust_on=request.original_adjust_on,
                    action=ModuleObjectActionFull.Create,
                    explanation=request.explanation,
                    conclusion=request.conclusion,
                )
                session.add(object_context)
                return Result(object_context=object_context, result_type=ResultType.CREATED)
            case ModuleObjectContextTable(hidden=True) as hidden_context:
                # Activate
                hidden_context.hidden = False
                hidden_context.modified_date = request.timepoint
                hidden_context.modified_by_id = request.user_uuid
                hidden_context.original_adjust_on = request.original_adjust_on
                hidden_context.explanation = request.explanation
                hidden_context.conclusion = request.conclusion
                session.add(hidden_context)
                return Result(object_context=hidden_context, result_type=ResultType.ACTIVATED)
            case _:
                return Result(object_context=existing_object_context, result_type=ResultType.ALREADY_EXIST)

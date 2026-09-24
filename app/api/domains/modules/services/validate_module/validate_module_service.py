from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field
from sqlalchemy.orm import Session

from app.api.domains.modules import ModuleObjectRepository
from app.api.domains.modules.types import ModuleObjectActionFull
from app.core.tables.modules import ModuleObjectsTable


class ValidateModuleObject(BaseModel):
    code: str
    object_id: int
    object_type: str
    title: str


class ValidateModuleSeverity(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"


class ValidateModuleError(BaseModel):
    rule: str
    object: ValidateModuleObject
    messages: list[str]
    severity: ValidateModuleSeverity = Field(default=ValidateModuleSeverity.error)


class ValidateModuleRequest(BaseModel):
    module_id: int
    module_objects: list[ModuleObjectsTable]

    _module_object_lookup: dict[str, ModuleObjectsTable] = PrivateAttr(default_factory=dict)

    def model_post_init(self, context: Any) -> None:
        self._module_object_lookup = {module_object.code: module_object for module_object in self.module_objects}

    def get_module_object(self, code: str) -> ModuleObjectsTable | None:
        return self._module_object_lookup.get(code, None)

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class ValidateModuleRule(ABC):
    @abstractmethod
    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        pass


class ValidateModuleResult(BaseModel):
    errors: list[ValidateModuleError]

    @computed_field
    @property
    def status(self) -> str:
        if not self.errors:
            return "OK"
        return "Failed"


class ValidateModuleService:
    def __init__(self, rules: list[ValidateModuleRule]):
        self._rules: list[ValidateModuleRule] = rules

    def validate(self, db: Session, request: ValidateModuleRequest) -> ValidateModuleResult:
        errors: list[ValidateModuleError] = []
        for rule in self._rules:
            errors += rule.validate(db, request)

        return ValidateModuleResult(
            errors=errors,
        )


class ValidateModuleRunner:
    def __init__(
        self,
        module_object_repository: ModuleObjectRepository,
        validate_module_service: ValidateModuleService,
    ):
        self._module_object_repository: ModuleObjectRepository = module_object_repository
        self._validate_module_service: ValidateModuleService = validate_module_service

    def run(self, session: Session, module_id: int) -> ValidateModuleResult:
        module_objects: list[ModuleObjectsTable] = self._module_object_repository.get_objects_in_time(
            session,
            module_id,
            datetime.now(UTC),
        )
        non_terminated_module_objects = [
            module_object
            for module_object in module_objects
            if module_object.module_object_context.action != ModuleObjectActionFull.Terminate
        ]
        request = ValidateModuleRequest(module_id=module_id, module_objects=non_terminated_module_objects)
        result: ValidateModuleResult = self._validate_module_service.validate(session, request)
        return result

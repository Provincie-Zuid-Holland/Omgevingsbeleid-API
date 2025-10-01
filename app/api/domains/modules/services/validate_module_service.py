from abc import ABC, ABCMeta, abstractmethod
from typing import Dict, List, Optional, Type
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError, computed_field
from sqlalchemy.orm import Session

from app.api.domains.publications.repository.publication_object_repository import PublicationObjectRepository
from app.core.tables.modules import ModuleObjectsTable


class ValidateModuleError(BaseModel, metaclass=ABCMeta):
    rule: str
    object_code: str
    messages: List[str]


class ValidationRule(ABC):
    @abstractmethod
    def validate(self, db: Session, module_objects: List[ModuleObjectsTable]) -> List[ValidateModuleError]:
        pass


class ValidateModuleResult(BaseModel):
    errors: List[ValidateModuleError]

    @computed_field
    @property
    def status(self) -> str:
        if self.errors == []:
            return "OK"
        return "Failed"


class ValidateModuleService:
    def __init__(self, rules: List[ValidationRule]):
        self._rules: List[ValidationRule] = rules
    
    # @todo: make "input" class for module_objects and module (ModuleTable) as 1 input class for this service
    def validate(self, db: Session, module_objects: List[ModuleObjectsTable]) -> ValidateModuleResult:
        errors: List[ValidateModuleError] = []
        for rule in self._rules:
            errors += rule.validate(db, module_objects)

        return ValidateModuleResult(
            errors=errors,
        )


class RequiredObjectFieldsRule(ValidationRule):
    def __init__(self, object_map: Dict[str, Type[BaseModel]]):
        self._object_map: Dict[str, Type[BaseModel]] = object_map
    
    def validate(self, db: Session, module_objects: List[ModuleObjectsTable]) -> List[ValidateModuleError]:
        errors: List[ValidateModuleError] = []

        for object_table in module_objects:
            model: Optional[Type[BaseModel]] = self._object_map.get(object_table.Object_Type)
            if not model:
                continue

            try:
                _ = model.model_validate(object_table)
            except ValidationError as e:
                errors.append(
                    ValidateModuleError(
                        rule="RequiredObjectFieldsRule",
                        object_code=object_table.Code,
                        messages=[f"{error['msg']} for {error['loc']}" for error in e.errors()],
                    )
                )
        return errors


class RequiredObjectFieldsRule(ValidationRule):
    def __init__(self, repository: PublicationObjectRepository):
        self._repository: PublicationObjectRepository = repository
    
    def validate(self, db: Session, module_objects: List[ModuleObjectsTable]) -> List[ValidateModuleError]:
        objects: List[dict] = self._repository.fetch_objects(
            db,
            request.module_id,
            datetime.now(timezone.utc),
        )
        existing_object_codes: Set[str] = {o.Code for o in objects}

        errors: List[ValidateModuleError] = []
        #@todo: iterate over module_objects
        # check if Hierachy_Code is not empty
        # if not empty, check if exists in existing_object_codes
        # if not exists = dangling obejct, create error to return
        return errors

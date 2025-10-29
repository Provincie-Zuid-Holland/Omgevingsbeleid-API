from abc import ABC, ABCMeta, abstractmethod
from datetime import timezone, datetime
from typing import Dict, List, Optional, Type, Set

from pydantic import BaseModel, ValidationError, computed_field, ConfigDict
from sqlalchemy.orm import Session

from app.api.domains.publications.repository.publication_object_repository import PublicationObjectRepository
from app.api.domains.werkingsgebieden.repositories.area_geometry_repository import AreaGeometryRepository
from app.api.domains.werkingsgebieden.repositories.geometry_repository import GeometryRepository, WerkingsgebiedHash
from app.core.tables.modules import ModuleObjectsTable
from app.core.tables.others import AreasTable


class ValidateModuleError(BaseModel, metaclass=ABCMeta):
    rule: str
    object_code: str
    messages: List[str]


class ValidateModuleRequest(BaseModel):
    module_id: int
    module_objects: List[ModuleObjectsTable]

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class ValidationRule(ABC):
    @abstractmethod
    def validate(self, db: Session, request: ValidateModuleRequest) -> List[ValidateModuleError]:
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

    def validate(self, db: Session, request: ValidateModuleRequest) -> ValidateModuleResult:
        errors: List[ValidateModuleError] = []
        for rule in self._rules:
            errors += rule.validate(db, request)

        return ValidateModuleResult(
            errors=errors,
        )


class RequiredObjectFieldsRule(ValidationRule):
    def __init__(self, object_map: Dict[str, Type[BaseModel]]):
        self._object_map: Dict[str, Type[BaseModel]] = object_map

    def validate(self, db: Session, request: ValidateModuleRequest) -> List[ValidateModuleError]:
        errors: List[ValidateModuleError] = []

        for object_table in request.module_objects:
            model: Optional[Type[BaseModel]] = self._object_map.get(object_table.Object_Type)
            if not model:
                continue

            try:
                _ = model.model_validate(object_table)
            except ValidationError as e:
                errors.append(
                    ValidateModuleError(
                        rule="required_object_fields_rule",
                        object_code=object_table.Code,
                        messages=[f"{error['msg']} for {error['loc']}" for error in e.errors()],
                    )
                )
        return errors


class RequiredHierarchyCodeRule(ValidationRule):
    def __init__(self, repository: PublicationObjectRepository):
        self._repository: PublicationObjectRepository = repository

    def validate(self, db: Session, request: ValidateModuleRequest) -> List[ValidateModuleError]:
        objects: List[dict] = self._repository.fetch_objects(
            db,
            request.module_id,
            datetime.now(timezone.utc),
        )
        existing_object_codes: Set[str] = {o["Code"] for o in objects}

        errors: List[ValidateModuleError] = []

        for object_info in objects:
            target_code = object_info.get("Hierarchy_Code")
            if target_code is None:
                continue

            if target_code not in existing_object_codes:
                errors.append(
                    ValidateModuleError(
                        rule="required_hierarchy_code_rule",
                        object_code=object_info.get("Code"),
                        messages=[f"Hierarchy code {target_code} does not exist"],
                    )
                )
        return errors


class NewestSourceWerkingsgebiedUsedRule(ValidationRule):
    def __init__(self, geometry_repository: GeometryRepository, area_geometry_repository: AreaGeometryRepository):
        self._geometry_repository: GeometryRepository = geometry_repository
        self._area_geometry_repository: AreaGeometryRepository = area_geometry_repository

    def validate(self, db: Session, request: ValidateModuleRequest) -> List[ValidateModuleError]:
        errors: List[ValidateModuleError] = []

        for object_table in request.module_objects:
            area_current: Optional[AreasTable] = object_table.Area
            if area_current is None:
                continue

            area_current_shape_hash: Optional[str] = self._area_geometry_repository.get_shape_hash(
                db, area_current.UUID
            )
            if area_current_shape_hash is None:
                errors.append(
                    ValidateModuleError(
                        rule="newest_source_werkingsgebied_used_rule",
                        object_code=object_table.Code,
                        messages=[f"Area {area_current.UUID} does not have a shape"],
                    )
                )
                continue

            area_title: str = area_current.Source_Title
            werkingsgebied_latest: Optional[WerkingsgebiedHash] = (
                self._geometry_repository.get_latest_shape_hash_by_title(db, area_title)
            )
            if werkingsgebied_latest is None:
                errors.append(
                    ValidateModuleError(
                        rule="newest_source_werkingsgebied_used_rule",
                        object_code=object_table.Code,
                        messages=[
                            f"Area {area_current.UUID} - '{area_current.Source_Title}' does not have a Werkingsgebieden shape"
                        ],
                    )
                )
                continue

            if area_current_shape_hash != werkingsgebied_latest.hash:
                errors.append(
                    ValidateModuleError(
                        rule="newest_source_werkingsgebied_used_rule",
                        object_code=object_table.Code,
                        messages=[
                            f"Area {area_current.UUID} - '{area_current.Source_Title}' does not use the latest known Werkingsgebieden shape {werkingsgebied_latest.UUID}"
                        ],
                    )
                )
                continue

        return errors

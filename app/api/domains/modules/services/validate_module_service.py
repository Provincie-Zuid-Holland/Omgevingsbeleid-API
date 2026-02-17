from abc import ABC, abstractmethod
from datetime import timezone, datetime
from typing import Dict, List, Optional, Type, Set

from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError, computed_field, ConfigDict
from sqlalchemy.orm import Session

from app.api.domains.publications.repository.publication_object_repository import PublicationObjectRepository
from app.api.domains.werkingsgebieden.repositories import InputGeoOnderverdelingRepository
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable
from app.core.tables.others import AreasTable


class ValidateModuleObject(BaseModel):
    code: str
    object_id: int
    object_type: str
    title: str


class ValidateModuleError(BaseModel):
    rule: str
    object: ValidateModuleObject
    messages: List[str]


class ValidateModuleRequest(BaseModel):
    module_id: int
    module_objects: List[ModuleObjectsTable]
    module_object_lookup: Dict[str, ModuleObjectsTable] = {}

    def get_module_object(self, code: str) -> Optional[ModuleObjectsTable]:
        if not self.module_object_lookup:
            self.module_object_lookup = {module_object.Code: module_object for module_object in self.module_objects}
        return self.module_object_lookup.get(code, None)

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class ValidateModuleRule(ABC):
    @abstractmethod
    def validate(self, db: Session, request: ValidateModuleRequest) -> List[ValidateModuleError]:
        pass


class ValidateModuleResult(BaseModel):
    errors: List[ValidateModuleError]

    @computed_field
    @property
    def status(self) -> str:
        if not self.errors:
            return "OK"
        return "Failed"


class ValidateModuleService:
    def __init__(self, rules: List[ValidateModuleRule]):
        self._rules: List[ValidateModuleRule] = rules

    def validate(self, db: Session, request: ValidateModuleRequest) -> ValidateModuleResult:
        errors: List[ValidateModuleError] = []
        for rule in self._rules:
            errors += rule.validate(db, request)

        return ValidateModuleResult(
            errors=errors,
        )


class RequiredObjectFieldsRule(ValidateModuleRule):
    def __init__(self, object_map: Dict[str, Type[BaseModel]]):
        self._object_map: Dict[str, Type[BaseModel]] = object_map

    def validate(self, db: Session, request: ValidateModuleRequest) -> List[ValidateModuleError]:
        errors: List[ValidateModuleError] = []

        for module_object_table in request.module_objects:
            model: Optional[Type[BaseModel]] = self._object_map.get(module_object_table.Object_Type)
            if not model:
                continue

            try:
                _ = model.model_validate(module_object_table)
            except ValidationError as e:
                errors.append(
                    ValidateModuleError(
                        rule="required_object_fields_rule",
                        object=ValidateModuleObject(
                            code=module_object_table.Code,
                            object_id=module_object_table.Object_ID,
                            object_type=module_object_table.Object_Type,
                            title=module_object_table.Title,
                        ),
                        messages=[f"{error['msg']} for {error['loc']}" for error in e.errors()],
                    )
                )
        return errors


class RequireExistingHierarchyCodeRule(ValidateModuleRule):
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
                module_object = request.get_module_object(object_info.get("Code"))
                title = module_object.Title if module_object and module_object.Title else ""

                errors.append(
                    ValidateModuleError(
                        rule="require_existing_hierarchy_code_rule",
                        object=ValidateModuleObject(
                            code=object_info.get("Code"),
                            object_id=object_info.get("Object_ID"),
                            object_type=object_info.get("Object_Type"),
                            title=title,
                        ),
                        messages=[f"Hierarchy code {target_code} does or will not exist in next version"],
                    )
                )
        return errors


class NewestInputGeoOnderverdelingUsedRule(ValidateModuleRule):
    def __init__(self, input_geo_onderverdeling_repository: InputGeoOnderverdelingRepository):
        self._input_geo_onderverdeling_repository: InputGeoOnderverdelingRepository = (
            input_geo_onderverdeling_repository
        )

    def validate(self, db: Session, request: ValidateModuleRequest) -> List[ValidateModuleError]:
        errors: List[ValidateModuleError] = []

        for object_table in request.module_objects:
            if object_table.Object_Type != "gebied":
                continue

            area_current: Optional[AreasTable] = object_table.Area
            if area_current is None:
                errors.append(
                    ValidateModuleError(
                        rule="newest_input_geo_onderverdeling_used_rule",
                        object=ValidateModuleObject(
                            code=object_table.Code,
                            object_id=object_table.Object_ID,
                            object_type=object_table.Object_Type,
                            title=object_table.Title,
                        ),
                        messages=["Object is of type 'gebied', but area is not known"],
                    )
                )
                continue

            area_hash: str = area_current.Source_Geometry_Hash or ""
            area_title: str = area_current.Source_Title
            onderverdeling = self._input_geo_onderverdeling_repository.get_by_title(db, area_title)
            if area_hash != onderverdeling.Geometry_Hash:
                errors.append(
                    ValidateModuleError(
                        rule="newest_input_geo_onderverdeling_used_rule",
                        object=ValidateModuleObject(
                            code=object_table.Code,
                            object_id=object_table.Object_ID,
                            object_type=object_table.Object_Type,
                            title=object_table.Title,
                        ),
                        messages=[
                            f"Area {area_current.UUID} does not use the latest known onderverdeling shape {onderverdeling.UUID}"
                        ],
                    )
                )
                continue

        return errors


class ForbidEmptyHtmlNodesRuleConfig(BaseModel):
    fields: List[str]
    html_void_elements: List[str]


class ForbidEmptyHtmlNodesRule(ValidateModuleRule):
    def __init__(self, main_config: MainConfig):
        self._config: ForbidEmptyHtmlNodesRuleConfig = main_config.get_as_model(
            "forbid_empty_html_nodes_rule",
            ForbidEmptyHtmlNodesRuleConfig,
        )

    def validate(self, db: Session, request: ValidateModuleRequest) -> List[ValidateModuleError]:
        errors: List[ValidateModuleError] = []

        for object_table in request.module_objects:
            for field_name in self._config.fields:
                value: str = str(getattr(object_table, field_name, ""))
                if self._has_empty_nodes(value):
                    errors.append(
                        ValidateModuleError(
                            rule="forbid_empty_html_nodes_rule",
                            object=ValidateModuleObject(
                                code=object_table.Code,
                                object_id=object_table.Object_ID,
                                object_type=object_table.Object_Type,
                                title=object_table.Title,
                            ),
                            messages=[f"Empty html node found in '{field_name}' for object {object_table.Code}"],
                        )
                    )

        return errors

    def _has_empty_nodes(self, text: str) -> bool:
        soup = BeautifulSoup(text, "html.parser")

        empty_tags = [
            tag
            for tag in soup.find_all(True)
            if tag.name not in self._config.html_void_elements
            and not tag.get_text(strip=True)
            and not any(child.name for child in tag.children)
        ]
        return bool(empty_tags)

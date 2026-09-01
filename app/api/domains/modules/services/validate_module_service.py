from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from bs4 import BeautifulSoup, PageElement, Tag
from dso import Gebiedsaanwijzingen, GebiedsaanwijzingenFactory, Thema
from dso.models import DocumentType
from dso.services.ow.gebiedsaanwijzingen.types import Gebiedsaanwijzing, GebiedsaanwijzingWaarde
from dso.services.ow.themas.thema import ThemaFactory
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, ValidationError, computed_field
from sqlalchemy.orm import Session

from app.api.domains.modules import ModuleObjectRepository
from app.api.domains.modules.types import ModuleObjectActionFull
from app.api.domains.others.repositories.hoofdlijn_repository import HoofdlijnRepository
from app.api.domains.publications.repository.publication_object_repository import PublicationObjectRepository
from app.api.domains.werkingsgebieden.repositories import InputGeoOnderverdelingRepository
from app.core.services import MainConfig
from app.core.tables.modules import ModuleObjectsTable
from app.core.tables.others import AreasTable
from app.core.tables.werkingsgebieden import InputGeoOnderverdelingenTable


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
        self._module_object_lookup = {module_object.Code: module_object for module_object in self.module_objects}

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


class RequiredObjectFieldsRule(ValidateModuleRule):
    def __init__(self, object_map: dict[str, type[BaseModel]]):
        self._object_map: dict[str, type[BaseModel]] = object_map

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []

        for module_object_table in request.module_objects:
            model: type[BaseModel] | None = self._object_map.get(module_object_table.Object_Type)
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

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        objects: list[dict] = self._repository.fetch_objects(
            db,
            request.module_id,
            datetime.now(UTC),
        )
        existing_object_codes: set[str] = {o["Code"] for o in objects}

        errors: list[ValidateModuleError] = []

        for object_info in objects:
            target_code = object_info.get("Hierarchy_Code")
            if target_code is None:
                continue

            if target_code not in existing_object_codes:
                module_object = request.get_module_object(object_info["Code"])
                title = module_object.Title if module_object and module_object.Title else ""

                errors.append(
                    ValidateModuleError(
                        rule="require_existing_hierarchy_code_rule",
                        object=ValidateModuleObject(
                            code=object_info["Code"],
                            object_id=object_info["Object_ID"],
                            object_type=object_info["Object_Type"],
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

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []

        for object_table in request.module_objects:
            if object_table.Object_Type != "gebied":
                continue

            area_current: AreasTable | None = object_table.Area
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
            onderverdeling: InputGeoOnderverdelingenTable | None = (
                self._input_geo_onderverdeling_repository.get_latest_by_title(db, area_title)
            )
            if onderverdeling is None:
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
                            f"The onderverdelingen lineage used by Area `{area_current.UUID}` with source title `{area_title}` can no longer be found in InputGeoOnderverdelingen"
                        ],
                        severity=ValidateModuleSeverity.warning,
                    )
                )
                continue

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
                        severity=ValidateModuleSeverity.warning,
                    )
                )
                continue

        return errors


class ForbiddenHtmlTagsRuleConfig(BaseModel):
    fields: list[str]
    forbidden_html_tags: list[str]


class ForbiddenHtmlTagsRule(ValidateModuleRule):
    def __init__(self, main_config: MainConfig):
        self._config: ForbiddenHtmlTagsRuleConfig = main_config.get_as_model(
            "forbidden_html_tags_rule",
            ForbiddenHtmlTagsRuleConfig,
        )

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []

        for object_table in request.module_objects:
            for field_name in self._config.fields:
                value: str = str(getattr(object_table, field_name, ""))
                maybe_forbidden_tag = self._has_forbidden_tags(value)
                if maybe_forbidden_tag:
                    errors.append(
                        ValidateModuleError(
                            rule="forbidden_html_tags_rule",
                            object=ValidateModuleObject(
                                code=object_table.Code,
                                object_id=object_table.Object_ID,
                                object_type=object_table.Object_Type,
                                title=object_table.Title,
                            ),
                            messages=[f"Forbidden html tag '{maybe_forbidden_tag}' found in '{field_name}'"],
                        )
                    )

        return errors

    def _has_forbidden_tags(self, text: str) -> str | None:
        soup = BeautifulSoup(text, "html.parser")
        for tag in self._config.forbidden_html_tags:
            elements = soup.find_all(tag)
            if elements:
                return tag
        return None


class ForbidEmptyHtmlNodesRuleConfig(BaseModel):
    fields: list[str]
    html_void_elements: list[str] = Field(default_factory=list)
    allowed_empty_when_sole_child: dict[str, list[str]] = Field(default_factory=dict)


class ForbidEmptyHtmlNodesRule(ValidateModuleRule):
    def __init__(self, main_config: MainConfig):
        self._config: ForbidEmptyHtmlNodesRuleConfig = main_config.get_as_model(
            "forbid_empty_html_nodes_rule",
            ForbidEmptyHtmlNodesRuleConfig,
        )

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []

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
        soup: BeautifulSoup = BeautifulSoup(text, "html.parser")

        for tag in soup.find_all(True):
            if tag.name in self._config.html_void_elements:
                continue
            if tag.get_text(strip=True):
                continue
            if any(child.name for child in tag.children):
                continue
            if self._is_allowed_empty_sole_child(tag):
                continue
            return True

        return False

    def _is_allowed_empty_sole_child(self, tag: Tag) -> bool:
        parent: Tag | None = tag.parent
        if parent is None:
            return False

        allowed_children: list[str] = self._config.allowed_empty_when_sole_child.get(parent.name, [])
        if tag.name not in allowed_children:
            return False

        # Only allowed when this empty tag is the single element child and the parent holds no other text,
        # so `<td><p></p></td>` passes but `<td><p>text</p><p></p></td>` does not.
        element_children: list[PageElement] = [child for child in parent.children if child.name]
        if len(element_children) != 1:
            return False
        return not parent.get_text(strip=True)


class AreaDesignationRefCheckRule(ValidateModuleRule):
    def __init__(self, dso_gebiedsaanwijzingen_factory: GebiedsaanwijzingenFactory):
        self._dso_gebiedsaanwijzingen_factory: GebiedsaanwijzingenFactory = dso_gebiedsaanwijzingen_factory

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []
        gebiedsaanwijzingen: Gebiedsaanwijzingen | None = self._dso_gebiedsaanwijzingen_factory.get_for_document(
            DocumentType.OMGEVINGSVISIE
        )

        for object_table in request.module_objects:
            if object_table.Object_Type != "gebiedsaanwijzing":
                continue

            ref_type: Gebiedsaanwijzing | None = gebiedsaanwijzingen.get_by_type_label(object_table.Ref_Type)
            if ref_type is None:
                errors.append(
                    ValidateModuleError(
                        rule="area_designation_check_ref_rule",
                        object=ValidateModuleObject(
                            code=object_table.Code,
                            object_id=object_table.Object_ID,
                            object_type=object_table.Object_Type,
                            title=object_table.Title,
                        ),
                        messages=[f"GebiedsaanwijzingType '{object_table.Ref_Type}' for gebiedsaanwijzing not found"],
                    )
                )
                continue
            if ref_type.aanwijzing_type.deprecated:
                errors.append(
                    ValidateModuleError(
                        rule="area_designation_check_ref_rule",
                        object=ValidateModuleObject(
                            code=object_table.Code,
                            object_id=object_table.Object_ID,
                            object_type=object_table.Object_Type,
                            title=object_table.Title,
                        ),
                        messages=[
                            f"GebiedsaanwijzingType '{object_table.Ref_Type}' for gebiedsaanwijzing is deprecated"
                        ],
                    )
                )
                continue

            ref_group: GebiedsaanwijzingWaarde | None = ref_type.get_value_by_label(object_table.Ref_Group)
            if ref_group is None:
                errors.append(
                    ValidateModuleError(
                        rule="area_designation_check_ref_rule",
                        object=ValidateModuleObject(
                            code=object_table.Code,
                            object_id=object_table.Object_ID,
                            object_type=object_table.Object_Type,
                            title=object_table.Title,
                        ),
                        messages=[
                            f"GebiedsaanwijzingGroep '{object_table.Ref_Group}' for GebiedsaanwijzingType '{object_table.Ref_Type}' not found"
                        ],
                    )
                )
                continue
            if ref_group.deprecated:
                errors.append(
                    ValidateModuleError(
                        rule="area_designation_check_ref_rule",
                        object=ValidateModuleObject(
                            code=object_table.Code,
                            object_id=object_table.Object_ID,
                            object_type=object_table.Object_Type,
                            title=object_table.Title,
                        ),
                        severity=ValidateModuleSeverity.warning,
                        messages=[
                            f"GebiedsaanwijzingGroep '{object_table.Ref_Group}' for GebiedsaanwijzingType '{object_table.Ref_Type}' is deprecated"
                        ],
                    )
                )
        return errors


class ThemasCheckRule(ValidateModuleRule):
    def __init__(self, dso_thema_factory: ThemaFactory):
        self._dso_thema_factory: ThemaFactory = dso_thema_factory

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []
        dso_themas: dict[str, Thema] = self._dso_thema_factory.get_all()

        for object_table in request.module_objects:
            if not object_table.Themas:
                continue

            for thema in object_table.Themas:
                dso_thema: Thema | None = dso_themas.get(thema)
                if dso_thema is None:
                    errors.append(
                        ValidateModuleError(
                            rule="themas_check_rule",
                            object=ValidateModuleObject(
                                code=object_table.Code,
                                object_id=object_table.Object_ID,
                                object_type=object_table.Object_Type,
                                title=object_table.Title,
                            ),
                            messages=[f"Thema '{thema}' can't be found in waardelijst"],
                        )
                    )
                elif dso_thema.deprecated:
                    errors.append(
                        ValidateModuleError(
                            rule="themas_check_rule",
                            object=ValidateModuleObject(
                                code=object_table.Code,
                                object_id=object_table.Object_ID,
                                object_type=object_table.Object_Type,
                                title=object_table.Title,
                            ),
                            messages=[f"Thema '{thema}' is deprecated"],
                        )
                    )
        return errors

@dataclass
class HoofdlijnenCheckRuleData:
    hoofdlijnen_uuids: set[UUID]
    object_table: ModuleObjectsTable

class HoofdlijnenCheckRule(ValidateModuleRule):
    def __init__(self, hoofdlijn_repository: HoofdlijnRepository):
        self._hoofdlijn_repository: HoofdlijnRepository = hoofdlijn_repository

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        object_data: list[HoofdlijnenCheckRuleData] = []
        hoofdlijn_set: set[UUID] = set()

        errors: list[ValidateModuleError] = []
        for object_table in request.module_objects:
            if object_table.Object_Type not in ["ambitie", "beleidsdoel", "beleidskeuze", "maatregel"]:
                continue

            if not object_table.Hoofdlijnen:
                continue
            hoofdlijnen_uuids: set[UUID] = {UUID(hoofdlijn_uuid) for hoofdlijn_uuid in object_table.Hoofdlijnen}
            object_data.append(HoofdlijnenCheckRuleData(hoofdlijnen_uuids=hoofdlijnen_uuids, object_table=object_table))
            hoofdlijn_set.update(hoofdlijnen_uuids)

        if not hoofdlijn_set:
            return errors

        found_hoofdlijnen_uuids: set[UUID] = self._hoofdlijn_repository.get_existing_uuids(db, hoofdlijn_set)
        missing_uuids = hoofdlijn_set - found_hoofdlijnen_uuids
        if not missing_uuids:
            return errors

        for data in object_data:
            missing_for_object: set[UUID] = data.hoofdlijnen_uuids & missing_uuids
            if missing_for_object:
                missing_displayed: list[str] = sorted(str(uuidx) for uuidx in missing_for_object)
                errors.append(
                    ValidateModuleError(
                        rule="hoofdlijnen_check_rule",
                        object=ValidateModuleObject(
                            code=data.object_table.Code,
                            object_id=data.object_table.Object_ID,
                            object_type=data.object_table.Object_Type,
                            title=data.object_table.Title,
                        ),
                        messages=[f"Hoofdlijnen with IDs {', '.join(missing_displayed)} are unknown"],
                    )
                )
        return errors


class CheckEmptyAreaDesignationTextConfig(BaseModel):
    fields: list[str]


class CheckEmptyAreaDesignationTextRule(ValidateModuleRule):
    def __init__(self, main_config: MainConfig):
        self._config: CheckEmptyAreaDesignationTextConfig = main_config.get_as_model(
            "check_empty_area_designation_text_rule",
            CheckEmptyAreaDesignationTextConfig,
        )

    def validate(self, db: Session, request: ValidateModuleRequest) -> list[ValidateModuleError]:
        errors: list[ValidateModuleError] = []

        for object_table in request.module_objects:
            for field_name in self._config.fields:
                value: str = str(getattr(object_table, field_name, ""))
                soup = BeautifulSoup(value, "html.parser")
                for gebiedsaanwijzing in soup.select('a[data-hint-type="gebiedsaanwijzing"]'):
                    inner_text = gebiedsaanwijzing.get_text(strip=True)
                    if len(inner_text) == 0:
                        errors.append(
                            ValidateModuleError(
                                rule="check_empty_area_designation_text_rule",
                                object=ValidateModuleObject(
                                    code=object_table.Code,
                                    object_id=object_table.Object_ID,
                                    object_type=object_table.Object_Type,
                                    title=object_table.Title,
                                ),
                                severity=ValidateModuleSeverity.warning,
                                messages=[
                                    f"Gebiedsaanwijzing '{gebiedsaanwijzing.get('data-code', '')}' in '{field_name}' has no selected text"
                                ],
                            )
                        )
        return errors


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
            if module_object.ModuleObjectContext.Action != ModuleObjectActionFull.Terminate
        ]
        request = ValidateModuleRequest(module_id=module_id, module_objects=non_terminated_module_objects)
        result: ValidateModuleResult = self._validate_module_service.validate(session, request)
        return result

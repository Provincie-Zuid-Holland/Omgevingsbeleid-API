import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Type, Optional, Set

from bs4 import BeautifulSoup, Tag, ResultSet
from dso import GebiedsaanwijzingenFactory, Gebiedsaanwijzingen
from dso.models import DocumentType
from dso.services.ow.gebiedsaanwijzingen.types import Gebiedsaanwijzing, GebiedsaanwijzingWaarde
from pydantic import BaseModel, Field, computed_field, ConfigDict, ValidationError
from sqlalchemy.orm import Session

from app.api.domains.publications.services.act_package.dso_act_input_data_builder import DOCUMENT_TYPE_MAP
from app.api.domains.publications.types.api_input_data import ApiActInputData, PublicationGio
from app.core.services import MainConfig


class ValidatePublicationObject(BaseModel):
    code: Optional[str] = None
    object_id: Optional[int] = None
    object_type: Optional[str] = None
    title: Optional[str] = None


class ValidatePublicationSeverity(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"


class ValidatePublicationError(BaseModel):
    rule: str
    object: ValidatePublicationObject = Field(default_factory=ValidatePublicationObject)
    messages: List[str]
    severity: ValidatePublicationSeverity = Field(default=ValidatePublicationSeverity.error)


class ValidatePublicationRequest(BaseModel):
    document_type: str
    input_data: ApiActInputData

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class ValidatePublicationException(Exception):
    def __init__(self, message: str, publication_errors: List[ValidatePublicationError] = []):
        super().__init__(message)
        self.message: str = message
        self.publication_errors = publication_errors

    def dump_errors(self):
        return [e.model_dump() for e in self.publication_errors]


class ValidatePublicationRule(ABC):
    @abstractmethod
    def validate(self, db: Session, request: ValidatePublicationRequest) -> List[ValidatePublicationError]:
        pass


class ValidatePublicationResult(BaseModel):
    errors: List[ValidatePublicationError]

    @computed_field
    @property
    def status(self) -> str:
        if not self.errors:
            return "OK"
        return "Failed"


class ValidatePublicationService:
    def __init__(self, rules: List[ValidatePublicationRule]):
        self._rules: List[ValidatePublicationRule] = rules

    def validate(self, db: Session, request: ValidatePublicationRequest) -> ValidatePublicationResult:
        errors: List[ValidatePublicationError] = []
        for rule in self._rules:
            errors += rule.validate(db, request)

        return ValidatePublicationResult(
            errors=errors,
        )


class RequiredObjectFieldsRule(ValidatePublicationRule):
    def __init__(self, document_type_map: Dict[str, Dict[str, Type[BaseModel]]]):
        self._document_type_map: Dict[str, Dict[str, Type[BaseModel]]] = document_type_map

    def validate(self, db: Session, request: ValidatePublicationRequest) -> List[ValidatePublicationError]:
        errors: List[ValidatePublicationError] = []

        object_map = self._document_type_map.get(request.document_type)

        for object_to_validate in request.input_data.Publication_Data.objects:
            model: Optional[Type[BaseModel]] = object_map.get(object_to_validate.get("Object_Type"))
            if not model:
                continue

            try:
                _ = model.model_validate(object_to_validate)
            except ValidationError as e:
                errors.append(
                    ValidatePublicationError(
                        rule="required_object_fields_rule",
                        object=ValidatePublicationObject(
                            code=object_to_validate.get("Code"),
                            object_id=object_to_validate.get("Object_ID"),
                            object_type=object_to_validate.get("Object_Type"),
                            title=object_to_validate.get("Title"),
                        ),
                        messages=[f"{error['msg']} for {error['loc']}" for error in e.errors()],
                    )
                )
        return errors


class UsedObjectsInPublicationExistInTemplateRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> List[ValidatePublicationError]:
        errors: List[ValidatePublicationError] = []

        publication_data_codes = [
            object_to_validate.get("Code") for object_to_validate in request.input_data.Publication_Data.objects
        ]
        for used_code_in_template in request.input_data.Publication_Data.used_object_codes:
            if used_code_in_template not in publication_data_codes:
                errors.append(
                    ValidatePublicationError(
                        rule="used_objects_in_publication_exist_in_template_rule",
                        object=ValidatePublicationObject(),  # there is no actual object to show in the error
                        messages=[
                            f"Object with code '{used_code_in_template}' used in template can't be found in publication"
                        ],
                    )
                )
        return errors


class UsedObjectInPublicationExistsRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> List[ValidatePublicationError]:
        errors: List[ValidatePublicationError] = []

        used_object_types_in_template: Set[str] = set()
        for used_object_code in request.input_data.Publication_Data.used_object_codes:
            object_type, _ = used_object_code.split("-")
            used_object_types_in_template.add(object_type)

        for object_code in request.input_data.Publication_Data.all_object_codes:
            object_type, object_id = object_code.split("-")
            if object_type not in used_object_types_in_template:
                continue

            if object_code not in request.input_data.Publication_Data.used_object_codes:
                errors.append(
                    ValidatePublicationError(
                        rule="used_object_in_publication_exists_rule",
                        object=ValidatePublicationObject(
                            code=object_code,
                            object_id=int(object_id),
                            object_type=object_type,
                        ),
                        messages=[f"Object {object_code} can't be found in publication"],
                    )
                )
        return errors


class UsedObjectTypeExistsRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> List[ValidatePublicationError]:
        errors: List[ValidatePublicationError] = []
        soup: BeautifulSoup = BeautifulSoup(request.input_data.Publication_Data.parsed_template, "html.parser")
        object_tags: ResultSet[Tag] = soup.find_all("object")
        objects: List[str] = [obj.get("code") for obj in object_tags if obj.get("code")]
        object_types: Set[str] = set(v.split("-", 1)[0] for v in objects)
        object_templates: Set[str] = request.input_data.Publication_Version.Publication.Template.Object_Templates.keys()

        for object_type in object_types:
            if object_type not in object_templates:
                errors.append(
                    ValidatePublicationError(
                        rule="used_object_type_exists_rule",
                        object=ValidatePublicationObject(
                            object_type=object_type,
                        ),
                        messages=[f"Object type '{object_type}' used in object template can't be found in publication"],
                    )
                )
        return errors


class ReferencedGebiedengroepCodeExistsRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> List[ValidatePublicationError]:
        errors: List[ValidatePublicationError] = []

        existing_gebiedengroepen: Set[str] = {
            gebiedengroep.code for gebiedengroep in request.input_data.Publication_Data.gebiedengroepen.values()
        }

        for used_object in request.input_data.Publication_Data.objects:
            gebiedengroep_code: Optional[str] = used_object.get("Gebiedengroep_Code")
            if not gebiedengroep_code:
                continue

            if gebiedengroep_code not in existing_gebiedengroepen:
                errors.append(
                    ValidatePublicationError(
                        rule="referenced_gebiedengroep_code_exists_rule",
                        object=ValidatePublicationObject(
                            code=used_object.get("Code"),
                            object_id=used_object.get("Object_ID"),
                            object_type=used_object.get("Object_Type"),
                            title=used_object.get("Title"),
                        ),
                        messages=[f"Gebiedengroep code '{gebiedengroep_code}' can't be found in publication"],
                    )
                )

        return errors


class GebiedengroepHasGiosRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> List[ValidatePublicationError]:
        errors: List[ValidatePublicationError] = []

        for gebiedengroep in request.input_data.Publication_Data.gebiedengroepen.values():
            if not gebiedengroep.gio_key:
                errors.append(
                    ValidatePublicationError(
                        rule="gebiedengroep_has_no_gio",
                        object=ValidatePublicationObject(
                            code=gebiedengroep.code,
                            title=gebiedengroep.title,
                        ),
                        messages=[f"Gebiedengroep code '{gebiedengroep.code}' has no valid gio"],
                    )
                )

        return errors


class GioDuplicateFilenameRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> List[ValidatePublicationError]:
        errors: List[ValidatePublicationError] = []
        gios: Dict[str, PublicationGio] = {}

        for publication_gio in request.input_data.Publication_Data.gios.values():
            dso_name: str = generate_dso_gio_name(publication_gio.title)
            if dso_name in gios.keys():
                duplicate_gio: PublicationGio = gios.get(dso_name)
                errors.append(
                    ValidatePublicationError(
                        rule="gio_duplicate_filename_rule",
                        object=ValidatePublicationObject(),
                        messages=[
                            f"GIO's [{publication_gio.key}, {duplicate_gio.key}] will generate the same name: '{dso_name}'"
                        ],
                    )
                )
            else:
                gios[dso_name] = publication_gio
        return errors


class GioUniqueRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> List[ValidatePublicationError]:
        errors: List[ValidatePublicationError] = []
        gios: Dict[str, PublicationGio] = {}

        for publication_gio in request.input_data.Publication_Data.gios.values():
            dso_name: str = generate_dso_gio_name(publication_gio.title)
            if dso_name in gios.keys():
                existing_gio = gios.get(dso_name)
                if publication_gio.source_codes == existing_gio.source_codes:
                    errors.append(
                        ValidatePublicationError(
                            rule="gio_unique_rule",
                            object=ValidatePublicationObject(),
                            messages=[
                                f"GIO's [{publication_gio.key}, {existing_gio.key}] have the same title '{dso_name}' and source codes {existing_gio.source_codes}"
                            ],
                        )
                    )
            else:
                gios.update({dso_name: publication_gio})
        return errors


class AreaDesignationRefCheckRule(ValidatePublicationRule):
    def __init__(self, dso_gebiedsaanwijzingen_factory: GebiedsaanwijzingenFactory):
        self._dso_gebiedsaanwijzingen_factory: GebiedsaanwijzingenFactory = dso_gebiedsaanwijzingen_factory

    def validate(self, db: Session, request: ValidatePublicationRequest) -> List[ValidatePublicationError]:
        errors: List[ValidatePublicationError] = []
        dso_document_type: DocumentType = DOCUMENT_TYPE_MAP[request.document_type]
        gebiedsaanwijzingen: Optional[Gebiedsaanwijzingen] = self._dso_gebiedsaanwijzingen_factory.get_for_document(
            dso_document_type
        )

        for gebiedsaanwijzing in request.input_data.Publication_Data.gebiedsaanwijzingen.values():
            object_type, object_id = gebiedsaanwijzing.code.split("-", 1)
            ref_type: Optional[Gebiedsaanwijzing] = gebiedsaanwijzingen.get_by_type_label(
                gebiedsaanwijzing.aanwijzing_type
            )

            if ref_type is None:
                errors.append(
                    ValidatePublicationError(
                        rule="area_designation_check_ref_rule",
                        object=ValidatePublicationObject(
                            code=gebiedsaanwijzing.code,
                            object_id=int(object_id),
                            object_type=object_type,
                            title=gebiedsaanwijzing.title,
                        ),
                        messages=[
                            f"GebiedsaanwijzingType '{gebiedsaanwijzing.aanwijzing_type}' for gebiedsaanwijzing not found"
                        ],
                    )
                )
                continue
            if ref_type.aanwijzing_type.deprecated:
                errors.append(
                    ValidatePublicationError(
                        rule="area_designation_check_ref_rule",
                        object=ValidatePublicationObject(
                            code=gebiedsaanwijzing.code,
                            object_id=int(object_id),
                            object_type=object_type,
                            title=gebiedsaanwijzing.title,
                        ),
                        messages=[
                            f"GebiedsaanwijzingType '{gebiedsaanwijzing.aanwijzing_type}' for gebiedsaanwijzing is deprecated"
                        ],
                    )
                )
                continue

            ref_group: Optional[GebiedsaanwijzingWaarde] = ref_type.get_value_by_label(
                gebiedsaanwijzing.aanwijzing_group
            )
            if ref_group is None:
                errors.append(
                    ValidatePublicationError(
                        rule="area_designation_check_ref_rule",
                        object=ValidatePublicationObject(
                            code=gebiedsaanwijzing.code,
                            object_id=int(object_id),
                            object_type=object_type,
                            title=gebiedsaanwijzing.title,
                        ),
                        messages=[
                            f"GebiedsaanwijzingGroep '{gebiedsaanwijzing.aanwijzing_group}' for GebiedsaanwijzingType '{gebiedsaanwijzing.aanwijzing_type}' not found"
                        ],
                    )
                )
                continue
            if ref_group.deprecated:
                errors.append(
                    ValidatePublicationError(
                        rule="area_designation_check_ref_rule",
                        object=ValidatePublicationObject(
                            code=gebiedsaanwijzing.code,
                            object_id=int(object_id),
                            object_type=object_type,
                            title=gebiedsaanwijzing.title,
                        ),
                        severity=ValidatePublicationSeverity.warning,
                        messages=[
                            f"GebiedsaanwijzingGroep '{gebiedsaanwijzing.aanwijzing_group}' for GebiedsaanwijzingType '{gebiedsaanwijzing.aanwijzing_type}' is deprecated"
                        ],
                    )
                )
        return errors


class ForbiddenHtmlTagsRuleConfig(BaseModel):
    fields: List[str]
    forbidden_html_tags: List[str]


class ForbiddenHtmlTagsRule(ValidatePublicationRule):
    def __init__(self, main_config: MainConfig):
        self._config: ForbiddenHtmlTagsRuleConfig = main_config.get_as_model(
            "forbidden_html_tags_rule",
            ForbiddenHtmlTagsRuleConfig,
        )

    def validate(self, db: Session, request: ValidatePublicationRequest) -> List[ValidatePublicationError]:
        errors: List[ValidatePublicationError] = []

        for used_object in request.input_data.Publication_Data.objects:
            for field_name in self._config.fields:
                value: str = str(used_object.get(field_name, ""))
                maybe_forbidden_tag = self._has_forbidden_tags(value)
                if maybe_forbidden_tag:
                    errors.append(
                        ValidatePublicationError(
                            rule="forbidden_html_tags_rule",
                            object=ValidatePublicationObject(
                                code=used_object.get("Code"),
                                object_id=used_object.get("Object_ID"),
                                object_type=used_object.get("Object_Type"),
                                title=used_object.get("Title"),
                            ),
                            messages=[f"Forbidden html tag '{maybe_forbidden_tag}' found in '{field_name}'"],
                        )
                    )

        return errors

    def _has_forbidden_tags(self, text: str) -> Optional[str]:
        soup = BeautifulSoup(text, "html.parser")
        for tag in self._config.forbidden_html_tags:
            elements = soup.find_all(tag)
            if elements:
                return tag
        return None


def generate_dso_gio_name(gio_title: str) -> str:
    s: str = gio_title.lower()
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    s = s.replace(" ", "-")
    return s


def validation_exception(errors: List[ValidatePublicationError]):
    return ValidatePublicationException(
        "Error(s) found while validating publication",
        publication_errors=errors,
    )

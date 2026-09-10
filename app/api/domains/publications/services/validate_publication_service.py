import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID

from bs4 import BeautifulSoup, ResultSet, Tag
from dso import Gebiedsaanwijzingen, GebiedsaanwijzingenFactory
from dso.models import DocumentType
from dso.services.koop.waardelijsten.gen import OnderwerpType, RechtsgebiedType
from dso.services.ow.gebiedsaanwijzingen.types import Gebiedsaanwijzing, GebiedsaanwijzingWaarde
from pydantic import BaseModel, ConfigDict, Field, ValidationError, computed_field
from sqlalchemy.orm import Session

from app.api.domains.others.repositories.hoofdlijn_repository import HoofdlijnRepository
from app.api.domains.publications.services.act_package.dso_act_input_data_builder import DOCUMENT_TYPE_MAP
from app.api.domains.publications.types.api_input_data import ApiActInputData, PublicationGio
from app.core.services import MainConfig


class ValidatePublicationObject(BaseModel):
    code: str | None = None
    object_id: int | None = None
    object_type: str | None = None
    title: str | None = None


class ValidatePublicationSeverity(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"


class ValidatePublicationError(BaseModel):
    rule: str
    object: ValidatePublicationObject = Field(default_factory=ValidatePublicationObject)
    messages: list[str]
    severity: ValidatePublicationSeverity = Field(default=ValidatePublicationSeverity.error)


class ValidatePublicationRequest(BaseModel):
    document_type: str
    input_data: ApiActInputData

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class ValidatePublicationException(Exception):
    def __init__(self, message: str, publication_errors: Sequence[ValidatePublicationError] = ()):
        super().__init__(message)
        self.message: str = message
        self.publication_errors = publication_errors

    def dump_errors(self):
        return [e.model_dump() for e in self.publication_errors]


class ValidatePublicationRule(ABC):
    @abstractmethod
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        pass


class ValidatePublicationResult(BaseModel):
    errors: list[ValidatePublicationError]

    @computed_field
    @property
    def status(self) -> str:
        if not self.errors:
            return "OK"
        return "Failed"


class ValidatePublicationService:
    def __init__(self, rules: list[ValidatePublicationRule]):
        self._rules: list[ValidatePublicationRule] = rules

    def validate(self, db: Session, request: ValidatePublicationRequest) -> ValidatePublicationResult:
        errors: list[ValidatePublicationError] = []
        for rule in self._rules:
            errors += rule.validate(db, request)

        return ValidatePublicationResult(
            errors=errors,
        )


class RequiredObjectFieldsRule(ValidatePublicationRule):
    def __init__(self, document_type_map: dict[str, dict[str, type[BaseModel]]]):
        self._document_type_map: dict[str, dict[str, type[BaseModel]]] = document_type_map

    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        object_map = self._document_type_map.get(request.document_type)

        for object_to_validate in request.input_data.Publication_Data.used_objects:
            model: type[BaseModel] | None = object_map.get(object_to_validate.get("Object_Type"))
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
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        publication_data_codes = [
            object_to_validate.get("Code") for object_to_validate in request.input_data.Publication_Data.used_objects
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
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        used_object_types_in_template: set[str] = set()
        for used_object_code in request.input_data.Publication_Data.used_object_codes:
            object_type, _ = used_object_code.split("-")
            used_object_types_in_template.add(object_type)

        for object_current in request.input_data.Publication_Data.all_objects:
            if object_current.get("Object_Type") not in used_object_types_in_template:
                continue

            if object_current.get("Code") not in request.input_data.Publication_Data.used_object_codes:
                errors.append(
                    ValidatePublicationError(
                        rule="used_object_in_publication_exists_rule",
                        object=ValidatePublicationObject(
                            code=object_current.get("Code"),
                            object_id=object_current.get("Object_ID"),
                            object_type=object_current.get("Object_Type"),
                            title=object_current.get("Title", ""),
                        ),
                        messages=[f"Object {object_current.get('Code')} can't be found in publication"],
                    )
                )
        return errors


class UsedObjectTypeExistsRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []
        soup: BeautifulSoup = BeautifulSoup(request.input_data.Publication_Data.parsed_template, "html.parser")
        object_tags: ResultSet[Tag] = soup.find_all("object")
        objects: list[str] = [obj.get("code") for obj in object_tags if obj.get("code")]
        object_types: set[str] = {v.split("-", 1)[0] for v in objects}
        object_templates: set[str] = request.input_data.Publication_Version.Publication.Template.Object_Templates.keys()

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
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        existing_gebiedengroepen: set[str] = {
            gebiedengroep.code for gebiedengroep in request.input_data.Publication_Data.gebiedengroepen.values()
        }

        for used_object in request.input_data.Publication_Data.used_objects:
            gebiedengroep_code: str | None = used_object.get("Gebiedengroep_Code")
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
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

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
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []
        gios: dict[str, PublicationGio] = {}

        for publication_gio in request.input_data.Publication_Data.gios.values():
            dso_name: str = generate_dso_gio_name(publication_gio.title)
            if dso_name in gios:
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
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []
        gios: dict[str, PublicationGio] = {}

        for publication_gio in request.input_data.Publication_Data.gios.values():
            dso_name: str = generate_dso_gio_name(publication_gio.title)
            if dso_name in gios:
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


class WaardelijstenValuesUsedCheckRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        koop_subjects: list[str] = [subject for subject in OnderwerpType.__members__]
        for subject in request.input_data.Publication_Version.Bill_Metadata["Subjects"]:
            if subject not in koop_subjects:
                errors.append(
                    ValidatePublicationError(
                        rule="waardelijsten_values_used_check_rule",
                        object=ValidatePublicationObject(),
                        messages=[
                            f"Subject '{subject}' is not known in waardelijst 'OnderwerpType'",
                        ],
                    )
                )

        koop_jurisdictions: list[str] = [subject for subject in RechtsgebiedType.__members__]
        for jurisdiction in request.input_data.Publication_Version.Bill_Metadata["Jurisdictions"]:
            if jurisdiction not in koop_jurisdictions:
                errors.append(
                    ValidatePublicationError(
                        rule="waardelijsten_values_used_check_rule",
                        object=ValidatePublicationObject(),
                        messages=[
                            f"Rechtsgebied '{jurisdiction}' is not known in waardelijst 'RechtsgebiedType'",
                        ],
                    )
                )
        return errors


class AreaDesignationRefCheckRule(ValidatePublicationRule):
    def __init__(self, dso_gebiedsaanwijzingen_factory: GebiedsaanwijzingenFactory):
        self._dso_gebiedsaanwijzingen_factory: GebiedsaanwijzingenFactory = dso_gebiedsaanwijzingen_factory

    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []
        dso_document_type: DocumentType = DOCUMENT_TYPE_MAP[request.document_type]
        gebiedsaanwijzingen: Gebiedsaanwijzingen | None = self._dso_gebiedsaanwijzingen_factory.get_for_document(
            dso_document_type
        )

        for gebiedsaanwijzing in request.input_data.Publication_Data.gebiedsaanwijzingen.values():
            object_type, object_id = gebiedsaanwijzing.code.split("-", 1)
            ref_type: Gebiedsaanwijzing | None = gebiedsaanwijzingen.get_by_type_label(
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

            ref_group: GebiedsaanwijzingWaarde | None = ref_type.get_value_by_label(gebiedsaanwijzing.aanwijzing_group)
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
    fields: list[str]
    forbidden_html_tags: list[str]


class ForbiddenHtmlTagsRule(ValidatePublicationRule):
    def __init__(self, main_config: MainConfig):
        self._config: ForbiddenHtmlTagsRuleConfig = main_config.get_as_model(
            "forbidden_html_tags_rule",
            ForbiddenHtmlTagsRuleConfig,
        )

    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        for used_object in request.input_data.Publication_Data.used_objects:
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

    def _has_forbidden_tags(self, text: str) -> str | None:
        soup = BeautifulSoup(text, "html.parser")
        for tag in self._config.forbidden_html_tags:
            elements = soup.find_all(tag)
            if elements:
                return tag
        return None


class BillCompactForbiddenTagsRuleConfig(BaseModel):
    fields: list[str]
    forbidden_tags: list[str]


class BillCompactForbiddenTagsRule(ValidatePublicationRule):
    def __init__(self, main_config: MainConfig):
        self._config: BillCompactForbiddenTagsRuleConfig = main_config.get_as_model(
            "bill_compact_forbidden_tags_rule",
            BillCompactForbiddenTagsRuleConfig,
        )

    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        bill_compact: dict[str, Any] = request.input_data.Publication_Version.Bill_Compact or {}
        for article_field in self._config.fields:
            article: str | None = bill_compact.get(article_field, None)
            if not article:
                continue

            soup = BeautifulSoup(article, "html.parser")
            for tag in self._config.forbidden_tags:
                tags = soup.find_all(tag)
                if len(tags) == 0:
                    continue
                errors.append(
                    ValidatePublicationError(
                        rule="bill_compact_forbidden_tags_rule",
                        object=ValidatePublicationObject(),
                        messages=[
                            f"Bill compact field {article_field} contains at least one forbidden tag: {tag.capitalize()}"
                        ],
                    )
                )
        return errors


class AttachmentInBillReferenceRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        errors: list[ValidatePublicationError] = []

        bill_compact: dict[str, Any] = request.input_data.Publication_Version.Bill_Compact or {}
        referenced_ids: set[int] = self._extract_ref_ids(bill_compact)

        attachment_ids: set[int] = set()
        attachment_title_map: dict[int, str] = {}

        for attachment in request.input_data.Publication_Data.bill_attachments:
            attachment_ids.add(attachment["id"])
            attachment_title_map[attachment["id"]] = attachment.get("title", attachment.get("filename", ""))

        unreferenced_attachments: set[int] = attachment_ids - referenced_ids
        for unreferenced_attachment_id in unreferenced_attachments:
            errors.append(
                ValidatePublicationError(
                    rule="attachment_in_bill_reference_rule",
                    object=ValidatePublicationObject(
                        object_id=unreferenced_attachment_id,
                        title=attachment_title_map.get(unreferenced_attachment_id, ""),
                    ),
                    messages=[f"Attachment with id '{unreferenced_attachment_id}' is not referenced in bill compact"],
                )
            )

        not_found_referenced_ids: set[int] = referenced_ids - attachment_ids

        for not_found_id in not_found_referenced_ids:
            errors.append(
                ValidatePublicationError(
                    rule="attachment_in_bill_reference_rule",
                    object=ValidatePublicationObject(
                        object_id=not_found_id,
                    ),
                    messages=[
                        f"Attachment with id '{not_found_id}' is referenced in bill compact but not found in attachments"
                    ],
                )
            )
        return errors

    def _extract_ref_ids(self, bill_compact: dict) -> set[int]:
        ref_ids: set[int] = set()
        pattern = re.compile(r"\[REF_BILL_PDF:(\d+)\]")

        for appendix in bill_compact.get("Appendices", []):
            matches = pattern.findall(appendix.get("Content", ""))
            for match in matches:
                ref_ids.add(int(match))

        motivation: dict | None = bill_compact.get("Motivation")
        if motivation:
            for appendix in motivation.get("Appendices", []):
                matches = pattern.findall(appendix.get("Content", ""))
                for match in matches:
                    ref_ids.add(int(match))
        return ref_ids


@dataclass
class HoofdlijnenCheckRuleData:
    hoofdlijnen_uuids: set[UUID]
    object_to_validate: dict


class HoofdlijnenCheckRuleConfig(BaseModel):
    fields: list[str]
    allowed_object_types: list[str]


class HoofdlijnenCheckRule(ValidatePublicationRule):
    def __init__(self, main_config: MainConfig, hoofdlijn_repository: HoofdlijnRepository):
        self._config: HoofdlijnenCheckRuleConfig = main_config.get_as_model(
            "hoofdlijnen_check_rule",
            HoofdlijnenCheckRuleConfig,
        )
        self._hoofdlijn_repository: HoofdlijnRepository = hoofdlijn_repository

    def validate(self, db: Session, request: ValidatePublicationRequest) -> list[ValidatePublicationError]:
        object_data: list[HoofdlijnenCheckRuleData] = []
        hoofdlijnen_set: set[UUID] = set()

        errors: list[ValidatePublicationError] = []
        for object_to_validate in request.input_data.Publication_Data.used_objects:
            if object_to_validate.get("Object_Type") not in self._config.allowed_object_types:
                continue

            for field in self._config.fields:
                field_value: list[str] | None = object_to_validate.get(field)
                if not field_value:
                    continue

                hoofdlijnen_uuids: set[UUID] = {UUID(hoofdlijn_uuid) for hoofdlijn_uuid in field_value}
                object_data.append(
                    HoofdlijnenCheckRuleData(hoofdlijnen_uuids=hoofdlijnen_uuids, object_to_validate=object_to_validate)
                )
                hoofdlijnen_set.update(hoofdlijnen_uuids)

        if not hoofdlijnen_set:
            return errors

        found_hoofdlijnen_uuids: set[UUID] = self._hoofdlijn_repository.get_existing_uuids(db, hoofdlijnen_set)
        missing_uuids = hoofdlijnen_set - found_hoofdlijnen_uuids
        if not missing_uuids:
            return errors

        for data in object_data:
            missing_for_object: set[UUID] = data.hoofdlijnen_uuids & missing_uuids
            if missing_for_object:
                missing_displayed: list[str] = sorted(str(uuidx) for uuidx in missing_for_object)
                errors.append(
                    ValidatePublicationError(
                        rule="hoofdlijnen_check_rule",
                        object=ValidatePublicationObject(
                            code=data.object_to_validate.get("Code"),
                            object_id=data.object_to_validate.get("Object_ID"),
                            object_type=data.object_to_validate.get("Object_Type"),
                            title=data.object_to_validate.get("Title"),
                        ),
                        messages=[f"Hoofdlijnen with IDs {', '.join(missing_displayed)} are unknown"],
                    )
                )
        return errors


def generate_dso_gio_name(gio_title: str) -> str:
    s: str = gio_title.lower()
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    s = s.replace(" ", "-")
    return s


def validation_exception(errors: list[ValidatePublicationError]):
    return ValidatePublicationException(
        "Error(s) found while validating publication",
        publication_errors=errors,
    )

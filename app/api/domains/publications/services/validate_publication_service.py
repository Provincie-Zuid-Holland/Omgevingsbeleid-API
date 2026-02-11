from abc import ABC, abstractmethod
from typing import Dict, List, Type, Optional, Set

from bs4 import BeautifulSoup, Tag, ResultSet
from pydantic import BaseModel, computed_field, ConfigDict, ValidationError
from sqlalchemy.orm import Session

from app.api.domains.publications.types.api_input_data import ApiActInputData


class ValidatePublicationObject(BaseModel):
    code: Optional[str] = None
    object_id: Optional[int] = None
    object_type: Optional[str] = None
    title: Optional[str] = None


class ValidatePublicationError(BaseModel):
    rule: str
    object: ValidatePublicationObject
    messages: List[str]


class ValidatePublicationRequest(BaseModel):
    document_type: str
    module_id: int
    input_data: ApiActInputData

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class ValidatePublicationException(Exception):
    def __init__(self, message: str, publication_errors: List[ValidatePublicationError] = None):
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
                        object=ValidatePublicationObject(
                            code=used_code_in_template,
                        ),
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

from abc import ABC, abstractmethod
from typing import Dict, List, Type, Optional

from pydantic import BaseModel, computed_field, ConfigDict, ValidationError
from sqlalchemy.orm import Session

from app.api.domains.publications.types.api_input_data import ApiActInputData


class ValidatePublicationObject(BaseModel):
    code: str
    object_id: int
    object_type: str
    title: str


class ValidatePublicationError(BaseModel):
    rule: str
    object: ValidatePublicationObject
    messages: List[str]


class ValidatePublicationRequest(BaseModel):
    document_type: str
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


class UsedObjectsExistRule(ValidatePublicationRule):
    def validate(self, db: Session, request: ValidatePublicationRequest) -> List[ValidatePublicationError]:
        errors: List[ValidatePublicationError] = []
        for object_to_validate in request.input_data.Publication_Data.objects:
            if object_to_validate.get("Code") not in request.input_data.Publication_Data.used_object_codes:
                errors.append(
                    ValidatePublicationError(
                        rule="used_objects_exist_rule",
                        object=ValidatePublicationObject(
                            code=object_to_validate.get("Code"),
                            object_id=object_to_validate.get("Object_ID"),
                            object_type=object_to_validate.get("Object_Type"),
                            title=object_to_validate.get("Title"),
                        ),
                        messages=[f"{object_to_validate.get('Code')} can't be found in codes used in template"],
                    )
                )
        return errors

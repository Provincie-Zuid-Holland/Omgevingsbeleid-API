from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, computed_field
from sqlalchemy.orm import Session

from app.api.domains.publications.types.api_input_data import ApiActInputData


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


def validation_exception(errors: list[ValidatePublicationError]):
    return ValidatePublicationException(
        "Error(s) found while validating publication",
        publication_errors=errors,
    )

from enum import Enum


class PurposeType(str, Enum):
    CONSOLIDATION = "consolidation"
    WITHDRAWAL = "withdrawal"


class DocumentType(str, Enum):
    VISION = "omgevingsvisie"
    PROGRAM = "programma"


class ProcedureType(str, Enum):
    DRAFT = "draft"
    FINAL = "final"


class PackageType(str, Enum):
    VALIDATION = "validation"
    PUBLICATION = "publication"


class ReportStatusType(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"
    VALID = "valid"
    FAILED = "failed"
    ABORTED = "aborted"


class MutationStrategy(str, Enum):
    RENVOOI = "renvooi"
    REPLACE = "replace"


class PublicationVersionStatus(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    ACTIVE = "active"
    VALIDATION = "validation"
    VALIDATION_FAILED = "validation_failed"
    PUBLICATION = "publication"
    PUBLICATION_FAILED = "publication_failed"
    PUBLICATION_ABORTED = "publication_aborted"
    ANNOUNCEMENT = "announcement"
    COMPLETED = "completed"


class PublicationType(str, Enum):
    ACT = "act"
    ANNOUNCEMENT = "announcement"

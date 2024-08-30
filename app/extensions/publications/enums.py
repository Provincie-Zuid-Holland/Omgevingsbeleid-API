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


class MutationStrategy(str, Enum):
    RENVOOI = "renvooi"
    REPLACE = "replace"

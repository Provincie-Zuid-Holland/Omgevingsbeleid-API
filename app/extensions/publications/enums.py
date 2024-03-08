from enum import Enum


class DocumentType(str, Enum):
    VISION = "Omgevingsvisie"
    PROGRAM = "Programma"


class ProcedureType(str, Enum):
    DRAFT = "Ontwerpbesluit"
    FINAL = "Definitief_besluit"


class PublicationActStatus(str, Enum):
    RESERVED = "Reserved"
    PENDING = "Pending"
    ACTIVE = "Active"
    REVOKED = "Revoked"


class PackageType(str, Enum):
    VALIDATION = "Validatie"
    PUBLICATION = "Publicatie"
    TERMINATE = "Afbreken"


class ValidationStatusType(str, Enum):
    PENDING = "Pending"
    VALID = "Valid"
    FAILED = "Failed"

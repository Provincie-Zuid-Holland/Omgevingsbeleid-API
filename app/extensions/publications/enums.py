from enum import Enum


class Document_Type(str, Enum):
    Vision = "Omgevingsvisie"
    Program = "Omgevingsprogramma"
    Ordinance = "Omgevingsverordening"


class Bill_Type(str, Enum):
    Concept = "Ontwerp"
    Final = "Definitief"


class Package_Event_Type(str, Enum):
    Validation = "Validatie"
    Publication = "Publicatie"
    Terminate = "Afbreken"

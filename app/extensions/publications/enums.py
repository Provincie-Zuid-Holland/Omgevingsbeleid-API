from enum import Enum


class DocumentType(str, Enum):
    VISION = "Omgevingsvisie"
    PROGRAM = "Omgevingsprogramma"
    ORDINANCE = "Omgevingsverordening"


class ProcedureType(str, Enum):
    CONCEPT = "Ontwerp"
    FINAL = "Definitief"


class PackageEventType(str, Enum):
    VALIDATION = "Validatie"
    PUBLICATION = "Publicatie"
    TERMINATE = "Afbreken"


class ValidationStatusType(str, Enum):
    """
    Status type of Publication Packages during the validation process.
    Defaults to Pending and is set to (in)Valid after report is uploaded.
    """

    PENDING = "Pending"
    VALID = "Valid"
    FAILED = "Failed"


class ProcedureStepType(str, Enum):
    """
    STOP ProcedureStappenDefinitief
    """

    DETERMINATION = "Vaststelling"
    SIGNING = "Ondertekening"
    PUBLICATION = "Publicatie"
    END_OBJECTION_PERIOD = "Einde_bezwaartermijn"
    END_APPEAL_PERIOD = "Einde_beroepstermijn"
    START_APPEAL_PROCEDURES = "Start_beroepsprocedures"
    SUSPENSION = "Schorsing"
    LIFT_SUSPENSION = "Opheffing_Schorsing"
    END_APPEAL_PROCEDURES = "Einde_beroepsprocedures"


class OWProcedureStatusType(str, Enum):
    CONCEPT = "Ontwerp"
    FINAL = "Definitief"


class OWAssociationType(str, Enum):
    """
    Every OWObject 1-to-many relationship is represented by an OWAssociation type
    """

    GEBIEDENGROEP_GEBIED = "Gebiedengroep_Gebied"
    TEKSTDEEL_LOCATION = "Tekstdeel_Locatie"


class IMOWTYPE(str, Enum):
    """
    IMOW 2.0.2
    """

    REGELTEKST = "regeltekst"
    GEBIED = "gebied"
    GEBIEDENGROEP = "gebiedengroep"
    LIJN = "lijn"
    LIJNENGROEP = "lijnengroep"
    PUNT = "punt"
    PUNTENGROEP = "puntengroep"
    ACTIVITEIT = "activiteit"
    GEBIEDSAANWIJZING = "gebiedsaanwijzing"
    OMGEVINGSWAARDE = "omgevingswaarde"
    OMGEVINGSNORM = "omgevingsnorm"
    PONS = "pons"
    KAART = "kaart"
    TEKSTDEEL = "tekstdeel"
    HOOFDLIJN = "hoofdlijn"
    DIVISIE = "divisie"
    KAARTLAAG = "kaartlaag"
    JURIDISCHEREGEL = "juridischeregel"
    ACTIVITEITLOCATIEAANDUIDING = "activiteitlocatieaanduiding"
    NORMWAARDE = "normwaarde"
    REGELINGSGEBIED = "regelingsgebied"
    AMBTSGEBIED = "ambtsgebied"
    DIVISIETEKST = "divisietekst"

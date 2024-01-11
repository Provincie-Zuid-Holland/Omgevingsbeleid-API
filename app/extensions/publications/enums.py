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
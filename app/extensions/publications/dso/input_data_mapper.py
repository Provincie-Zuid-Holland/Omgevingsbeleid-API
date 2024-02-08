from typing import Dict, List

import dso.models as dso_models
from dso.builder.state_manager.input_data.besluit import Artikel, Besluit
from dso.builder.state_manager.input_data.input_data_loader import InputData
from dso.builder.state_manager.input_data.object_template_repository import ObjectTemplateRepository
from dso.builder.state_manager.input_data.regeling import Regeling
from dso.builder.state_manager.input_data.resource.asset.asset_repository import AssetRepository
from dso.builder.state_manager.input_data.resource.policy_object.policy_object_repository import PolicyObjectRepository
from dso.builder.state_manager.input_data.resource.resources import Resources
from dso.builder.state_manager.input_data.resource.werkingsgebied.werkingsgebied_repository import (
    WerkingsgebiedRepository,
)

from app.extensions.publications.enums import DocumentType, PackageEventType, ProcedureType
from app.extensions.publications.models import (
    ProcedureStep,
    Publication,
    PublicationBill,
    PublicationConfig,
    PublicationPackage,
)

DOCUMENT_TYPE_MAP = {
    DocumentType.VISION: "OMGEVINGSVISIE",
    DocumentType.PROGRAM: "PROGRAMMA",
    DocumentType.ORDINANCE: "VERORDENING",
}

OPDRACHT_TYPE_MAP = {
    PackageEventType.VALIDATION: "VALIDATIE",
    PackageEventType.PUBLICATION: "PUBLICATIE",
}


def get_opdracht_type(package_event_type: PackageEventType) -> str:
    return OPDRACHT_TYPE_MAP.get(package_event_type, "PUBLICATIE")


def get_document_type(document_type: DocumentType) -> str:
    if document_type == DocumentType.ORDINANCE:
        raise NotImplementedError(f"Document type {document_type} not supported")
    return DOCUMENT_TYPE_MAP.get(document_type, "")


def get_procedure_type(procedure_type: ProcedureType) -> str:
    if procedure_type == ProcedureType.CONCEPT:
        return "Ontwerpbesluit"
    if procedure_type == ProcedureType.FINAL:
        return "Definitief_besluit"
    else:
        raise ValueError(f"Unknown procedure type: {procedure_type}")


def map_dso_input_data(
    publication: Publication,
    bill: PublicationBill,
    package: PublicationPackage,
    config: PublicationConfig,
    aggregated_objects: Dict[str, List[dict]],
    free_text_template_str: str,
    object_template_repository: ObjectTemplateRepository,
    asset_repository: AssetRepository,
    werkingsgebied_repository: WerkingsgebiedRepository,
    policy_object_repository: PolicyObjectRepository,
):
    bekendmakingsdatum = str(package.Announcement_Date)
    tekst_artikelen = [
        Artikel(
            label=art.Label,
            inhoud=art.Content,
        )
        for art in bill.Bill_Data.Articles
    ]

    dso_bill = Besluit(
        officiele_titel=bill.Bill_Data.Bill_Title,
        regeling_opschrift=bill.Bill_Data.Regulation_Title,
        aanhef=bill.Bill_Data.Preamble,
        wijzig_artikel=Artikel(
            label=bill.Bill_Data.Amendment_Article.Label,
            inhoud=bill.Bill_Data.Amendment_Article.Content,
        ),
        tekst_artikelen=tekst_artikelen,
        tijd_artikel=Artikel(
            label=bill.Bill_Data.Time_Article.Label,
            inhoud=bill.Bill_Data.Time_Article.Content,
        ),
        sluiting=bill.Bill_Data.Closing,
        ondertekening=bill.Bill_Data.Signature,
        rechtsgebieden=[config.Jurisdiction],
        onderwerpen=[config.Subjects],
        soort_procedure=get_procedure_type(bill.Procedure_Type),
    )

    # Convert procudure steps
    procedure = dso_models.ProcedureVerloop(
        bekend_op=str(bill.Procedure_Data.Announcement_Date),
        stappen=[
            dso_models.ProcedureStap(
                soort_stap=step.Step_Type.value,
                voltooid_op=str(step.Conclusion_Date),
            )
            for step in bill.Procedure_Data.Steps
        ],
    )

    resources = Resources(
        policy_object_repository=policy_object_repository,
        asset_repository=asset_repository,
        werkingsgebied_repository=werkingsgebied_repository,
    )

    # Create inputdata
    input_data = InputData(
        publication_settings=dso_models.PublicationSettings(
            document_type=get_document_type(publication.Document_Type),
            datum_bekendmaking=bekendmakingsdatum,
            datum_juridisch_werkend_vanaf=str(bill.Effective_Date),
            provincie_id=config.Province_ID,
            wId_suffix=package.FRBR_Info.bill_expression_version,
            soort_bestuursorgaan=config.Governing_Body_Type,  # Provinciale_states "/tooi/def/thes/kern/c_411b4e4a"
            expression_taal=package.FRBR_Info.bill_expression_lang,
            regeling_componentnaam=config.Act_Componentname,  # nieuweregeling
            opdracht={
                "opdracht_type": get_opdracht_type(package.Package_Event_Type),
                "id_levering": str(package.UUID),
                "id_bevoegdgezag": str(config.Authority_ID),
                "id_aanleveraar": str(config.Submitter_ID),
                "publicatie_bestand": package.FRBR_Info.as_filename(),
                "datum_bekendmaking": bekendmakingsdatum,
            },
            doel=dso_models.Doel(
                jaar=str(package.FRBR_Info.get_target_info()["year"]),
                naam=package.FRBR_Info.get_target_info()["target_name"],
            ),
            besluit_frbr=package.FRBR_Info.get_besluit_frbr(),
            regeling_frbr=package.FRBR_Info.get_regeling_frbr(),
        ),
        besluit=dso_bill,
        regeling=Regeling(
            versienummer=package.FRBR_Info.act_expression_version,
            officiele_titel=bill.Bill_Data.Regulation_Title,
            citeertitel=bill.Bill_Data.Regulation_Title,  # TODO: add citation title?
            is_officieel=bill.Is_Official,
            rechtsgebieden=[config.Jurisdiction],
            onderwerpen=[config.Subjects],
        ),
        regeling_vrijetekst=free_text_template_str,
        procedure_verloop=procedure,
        resources=resources,
        object_template_repository=object_template_repository,
    )
    return input_data

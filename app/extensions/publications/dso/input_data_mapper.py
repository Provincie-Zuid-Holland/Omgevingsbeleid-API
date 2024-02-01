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

from app.extensions.publications.enums import Document_Type, Procedure_Type
from app.extensions.publications.models import PublicationBill, PublicationConfig, PublicationPackage


def map_dso_input_data(
    publication: PublicationBill,
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
    bekendmakingsdatum = package.Announcement_Date.strftime("%Y-%m-%d")
    opdracht_type = {"Validatie": "VALIDATIE", "Publicatie": "PUBLICATIE"}.get(package.Package_Event_Type, "PUBLICATIE")

    # TODO: change db column to use same values to skip this step
    soort_procedure = "Definitief_besluit"
    if bill.Procedure_Type == Procedure_Type.CONCEPT:
        soort_procedure = "Ontwerpbesluit"

    dso_bill = Besluit(
        officiele_titel=bill.Bill_Data.Bill_Title,
        regeling_opschrift=bill.Bill_Data.Regulation_Title,
        aanhef=bill.Bill_Data.Preamble,
        wijzig_artikel=Artikel(
            label=bill.Bill_Data.Amendment_Article.Label,
            inhoud=bill.Bill_Data.Amendment_Article.Content,
        ),
        tekst_artikelen=[],
        tijd_artikel=Artikel(
            label=bill.Bill_Data.Amendment_Article.Label,
            inhoud=bill.Bill_Data.Amendment_Article.Content,
        ),  # TODO: add time article seperate in Bill_Data?
        sluiting=bill.Bill_Data.Closing,
        ondertekening=bill.Bill_Data.Signature,
        rechtsgebieden=[config.Jurisdiction],
        onderwerpen=[config.Subjects],
        soort_procedure=soort_procedure,
    )
    for article in bill.Bill_Data.Articles:
        dso_bill.tekst_artikelen.append(
            Artikel(
                label=article.Label,
                inhoud=article.Content,
            )
        )

    # convert procudure steps
    procedure = dso_models.ProcedureVerloop(
        bekend_op=bill.Procedure_Data.Announcement_Date.strftime("%Y-%m-%d"),
        stappen=[],
    )
    for step in bill.Procedure_Data.Steps:
        procedure.stappen.append(
            dso_models.ProcedureStap(
                soort_stap=step.Procedure_Step_Type,
                voltooid_op=step.Completed_Date.strftime("%Y-%m-%d"),
            )
        )

    resources = Resources(
        policy_object_repository=policy_object_repository,
        asset_repository=asset_repository,
        werkingsgebied_repository=werkingsgebied_repository,
    )

    document_type_mapping = {
        Document_Type.VISION: "VISIE",
        Document_Type.PROGRAM: "PROGRAMMA",
        Document_Type.ORDINANCE: "VERORDENING",
    }
    document_type = document_type_mapping.get(publication.Document_Type, None)
    if document_type == "VERORDENING":
        raise NotImplementedError(f"Document type {publication.Document_Type} not supported")

    # Create inputdata
    input_data = InputData(
        publication_settings=dso_models.PublicationSettings(
            document_type=document_type,
            datum_bekendmaking=bekendmakingsdatum,
            datum_juridisch_werkend_vanaf=bill.Effective_Date.strftime("%Y-%m-%d"),
            provincie_id=config.Province_ID,
            wId_suffix=package.FRBR_Info.bill_expression_version,
            soort_bestuursorgaan="/tooi/def/thes/kern/c_411b4e4a",
            expression_taal=package.FRBR_Info.bill_expression_lang,
            regeling_componentnaam="nieuweregeling",
            provincie_ref=f"/tooi/id/provincie/{config.Province_ID}",
            opdracht={
                "opdracht_type": opdracht_type,
                "id_levering": str(package.UUID),
                "id_bevoegdgezag": str(config.Authority_ID),
                "id_aanleveraar": str(config.Submitter_ID),
                "publicatie_bestand": package.FRBR_Info.as_filename(),
                "datum_bekendmaking": bekendmakingsdatum,
            },
            doel=dso_models.Doel(jaar="2024", naam="InstellingOmgevingsvisie"),  # TODO insert Doel from bill/package
            besluit_frbr=package.FRBR_Info.get_besluit_frbr(),
            regeling_frbr=package.FRBR_Info.get_regeling_frbr(),
        ),
        besluit=dso_bill,
        regeling=Regeling(
            versienummer="1",
            officiele_titel=bill.Bill_Data.Regulation_Title,
            citeertitel=bill.Bill_Data.Regulation_Title,  # TODO: add citation title
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

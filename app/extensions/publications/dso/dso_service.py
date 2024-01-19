from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from sqlalchemy.orm import Session

from dso.builder.builder import Builder
from dso.builder.state_manager.input_data.input_data_loader import InputData
import dso.models as dso_models
from dso.builder.state_manager.input_data.besluit import Artikel, Besluit
from dso.builder.state_manager.input_data.input_data_loader import InputData
from dso.builder.state_manager.input_data.object_template_repository import ObjectTemplateRepository
from dso.builder.state_manager.input_data.regeling import Regeling
from dso.builder.state_manager.input_data.resource.asset.asset_repository import AssetRepository
from dso.builder.state_manager.input_data.resource.policy_object.policy_object_repository import (
    PolicyObjectRepository,
)
from dso.builder.state_manager.input_data.resource.resources import Resources
from dso.builder.state_manager.input_data.resource.werkingsgebied.werkingsgebied_repository import (
    WerkingsgebiedRepository,
)

from app.extensions.publications.dso.templates import create_vrijetekst_template, object_templates
from app.extensions.publications.models import (
    PublicationBill,
    PublicationConfig,
    PublicationPackage,
)
from app.extensions.publications.repository.publication_object_repository import (
    PublicationObjectRepository,
)
from app.extensions.publications.repository.publication_repository import PublicationRepository
from app.extensions.publications.tables.tables import (
    PublicationBillTable,
    PublicationConfigTable,
    PublicationPackageTable,
)


class DSOService:
    def __init__(self, db: Session):
        self._db: Session = db

    def get_policy_object_repository(self, aggregated_objects: Dict[str, List[dict]]):
        repository = PolicyObjectRepository()
        for objects in aggregated_objects.values():
            for o in objects:
                repository.add(o["Code"], o)
        return repository

    def get_asset_repository(self):
        repository = AssetRepository()
        return repository

    def get_werkingsgebied_repository(self, org_id: str, country_code: str):
        repository = WerkingsgebiedRepository(org_id, country_code)
        return repository

    def get_object_template_repository(self, object_templates):
        repository = ObjectTemplateRepository(object_templates)
        return repository

    def convert_to_dso_models(
        self,
        bill: PublicationBill,
        package: PublicationPackage,
        config: PublicationConfig,
        aggregated_objects: Dict[str, List[dict]],
        vrijetekst_template: str,
    ):
        bekendmakingsdatum = bill.Announcement_Date.strftime("%Y-%m-%d")
        opdracht_type = {"Validatie": "VALIDATIE", "Publicatie": "PUBLICATIE"}.get(
            package.Package_Event_Type, "PUBLICATIE"
        )

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
            soort_procedure="Definitief_besluit",
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
            policy_object_repository=self.get_policy_object_repository(aggregated_objects),
            asset_repository=self.get_asset_repository(),
            werkingsgebied_repository=self.get_werkingsgebied_repository(
                config.Province_ID, "nld"
            ),
        )

        # Create inputdata
        input_data = InputData(
            publication_settings=dso_models.PublicationSettings(
                document_type="VISIE" if bill.Document_Type == "Omgevingsvisie" else "PROGRAMMA",
                datum_bekendmaking=bekendmakingsdatum,
                datum_juridisch_werkend_vanaf=bill.Effective_Date.strftime("%Y-%m-%d"),
                provincie_id=config.Province_ID,
                wId_suffix="1",
                soort_bestuursorgaan="/tooi/def/thes/kern/c_411b4e4a",
                expression_taal="nld",
                regeling_componentnaam="nieuweregeling",
                provincie_ref="/tooi/id/provincie/pv28",
                opdracht={
                    "opdracht_type": opdracht_type,
                    "id_levering": str(package.UUID),
                    "id_bevoegdgezag": str(package.Authority_ID),
                    "id_aanleveraar": str(package.Submitter_ID),
                    "publicatie_bestand": package.Publication_Filename,
                    "datum_bekendmaking": bekendmakingsdatum,
                },
                doel=dso_models.Doel(jaar="2024", naam="InstellingOmgevingsvisie"),
                besluit_frbr={
                    "work_land": "nl",
                    "work_datum": "2024",
                    "work_overig": "2_2093",
                    "expression_taal": "nld",
                    "expression_datum": "2024-01-05",
                    "expression_versie": "2093",
                    "expression_overig": None,
                },
                regeling_frbr={
                    "work_land": "nl",
                    "work_datum": "2024",
                    "work_overig": "2_89",
                    "expression_taal": "nld",
                    "expression_datum": "2024-01-05",
                    "expression_versie": "89",
                    "expression_overig": None,
                },
            ),
            besluit=dso_bill,
            regeling=Regeling(
                versienummer="1",
                officiele_titel=bill.Bill_Data.Regulation_Title,
                citeertitel=bill.Bill_Data.Regulation_Title,  # TODO: add citation title
                is_officieel="true",
                rechtsgebieden=[config.Jurisdiction],
                onderwerpen=[config.Subjects],
            ),
            regeling_vrijetekst=vrijetekst_template,
            procedure_verloop=procedure,
            resources=resources,
            object_template_repository=self.get_object_template_repository(object_templates),
        )
        return input_data

    def prepare_input_data(self, bill, package, config):
        repository = PublicationObjectRepository(self._db)
        objects = repository.fetch_objects(
            module_id=1,
            timepoint=datetime.utcnow(),
            object_types=[
                "visie_algemeen",
                "ambitie",
                "beleidskeuze",
            ],
            field_map=[
                "UUID",
                "Object_Type",
                "Object_ID",
                "Code",
                "Title",
                "Description",
                "Hierarchy_Code",
            ],
        )

        aggregated_objects = defaultdict(list)
        for o in objects:
            aggregated_objects[o["Object_Type"]].append(o)

        base_template = create_vrijetekst_template()
        vrijetekst_template = base_template.render(
            **aggregated_objects,
        )

        input_data: InputData = self.convert_to_dso_models(
            bill,
            package,
            config,
            aggregated_objects,
            vrijetekst_template,
        )
        return input_data

    def build_dso_package(self, input_data):
        builder = Builder(input_data)
        builder.build_publication_files()
        builder.save_files("./output-dso")

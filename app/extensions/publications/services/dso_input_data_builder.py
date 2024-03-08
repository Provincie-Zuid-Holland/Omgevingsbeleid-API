from typing import List, Optional
import uuid

from dso.builder.state_manager.input_data.input_data_loader import InputData
from app.extensions.publications.enums import DocumentType, PackageType
from app.extensions.publications.models import PublicationEnvironment, PublicationTemplate
from app.extensions.publications.services.act_frbr_provider import ActFrbr
from app.extensions.publications.services.bill_frbr_provider import BillFrbr
from app.extensions.publications.services.publication_data_provider import PublicationData

from app.extensions.publications.tables.tables import PublicationEnvironmentTable, PublicationTable, PublicationTemplateTable, PublicationVersionTable

import dso.models as dso_models
from dso.builder.state_manager.input_data.besluit import Artikel, Besluit
from dso.builder.state_manager.input_data.input_data_loader import InputData
from dso.builder.state_manager.input_data.object_template_repository import ObjectTemplateRepository
from dso.builder.state_manager.input_data.regeling import Regeling
from dso.builder.state_manager.input_data.resource.asset.asset_repository import AssetRepository as DSOAssetRepository
from dso.builder.state_manager.input_data.resource.policy_object.policy_object_repository import PolicyObjectRepository
from dso.builder.state_manager.input_data.resource.resources import Resources
from dso.builder.state_manager.input_data.resource.werkingsgebied.werkingsgebied_repository import (
    WerkingsgebiedRepository,
)

from app.extensions.publications.waardelijsten import Bestuursorgaan, Onderwerp, Rechtsgebied


DOCUMENT_TYPE_MAP = {
    DocumentType.VISION: "OMGEVINGSVISIE",
    DocumentType.PROGRAM: "PROGRAMMA",
}

OPDRACHT_TYPE_MAP = {
    PackageType.VALIDATION: "VALIDATIE",
    PackageType.PUBLICATION: "PUBLICATIE",
}


class DsoInputDataBuilder:
    def __init__(
        self,
        publication_version: PublicationVersionTable,
        package_type: PackageType,
        bill_frbr: BillFrbr,
        act_frbr: ActFrbr,
        publication_data: PublicationData,
    ):
        self._publication_version: PublicationVersionTable = publication_version
        self._package_type: PackageType = package_type
        self._bill_frbr: BillFrbr = bill_frbr
        self._act_frbr: ActFrbr = act_frbr
        self._publication_data: PublicationData = publication_data
        self._publication: PublicationTable = publication_version.Publication
        self._environment: PublicationEnvironmentTable = publication_version.Environment
        self._template: PublicationTemplateTable = self._publication.Template

    def build(self) -> InputData:
        input_data: InputData = InputData(
            publication_settings=self._get_publication_settings(),
            besluit=self._get_besluit(),
            regeling=self._get_regeling(),
            regeling_vrijetekst=self._publication_data.parsed_template,
            procedure_verloop=self._get_procedure_verloop(),
            resources=self._get_resources(),
            object_template_repository=self._get_object_template_repository(),
            ambtsgebied=self._get_ambtsgebied(),
        )
        return input_data

    def _get_publication_settings(self) -> dso_models.PublicationSettings:
        dso_document_type: str = DOCUMENT_TYPE_MAP[self._publication.Document_Type]
        dso_opdracht_type: str = OPDRACHT_TYPE_MAP[self._package_type]

        publication_settings = dso_models.PublicationSettings(
            document_type=dso_document_type,
            datum_bekendmaking=self._publication_version.Announcement_Date.strftime('%Y-%m-%d'),
            datum_juridisch_werkend_vanaf=self._publication_version.Effective_Date.strftime('%Y-%m-%d'),
            provincie_id=self._environment.Province_ID,
            wId_suffix=self._act_frbr.Expression_Version,
            soort_bestuursorgaan=self._get_soort_bestuursorgaan(),

            # @todo: This should be moved to Werkingsgebieden which is the only one that uses this
            expression_taal=self._act_frbr.Expression_Language,

            regeling_componentnaam=self._act_frbr.Component_Name,
            provincie_ref=f"/tooi/id/provincie/{self._environment.Province_ID}",
            opdracht={
                "opdracht_type": dso_opdracht_type,
                "id_levering": str(uuid.uuid4()),
                "id_bevoegdgezag": self._environment.Authority_ID,
                "id_aanleveraar": self._environment.Submitter_ID,
                "publicatie_bestand": f"akn_nl_bill_{self._environment.Province_ID}-{self._bill_frbr.Work_Country}-{self._bill_frbr.Work_Other}.xml",
                "datum_bekendmaking": "2024-02-28",
            },
            doel=dso_models.Doel(jaar="2024", naam=f"instelling-{self._act_frbr.Work_Other}-{self._act_frbr.Expression_Version}"),
            besluit_frbr={
                "work_land": self._bill_frbr.Work_Country,
                "work_datum": self._bill_frbr.Work_Date,
                "work_overig": self._bill_frbr.Work_Other,
                "expression_taal": self._bill_frbr.Expression_Language,
                "expression_datum": self._bill_frbr.Expression_Date,
                "expression_versie": self._bill_frbr.Expression_Version,
                "expression_overig": self._bill_frbr.Expression_Other,
            },
            regeling_frbr={
                "work_land": self._act_frbr.Work_Country,
                "work_datum": self._act_frbr.Work_Date,
                "work_overig": self._act_frbr.Work_Other,
                "expression_taal": self._act_frbr.Expression_Language,
                "expression_datum": self._act_frbr.Expression_Date,
                "expression_versie": self._act_frbr.Expression_Version,
                "expression_overig": self._act_frbr.Expression_Other,
            },
        )
        return publication_settings

    def _get_besluit(self) -> Besluit:
        besluit = Besluit(
            officiele_titel=self._publication_version.Bill_Metadata["OfficialTitle"],
            regeling_opschrift=self._publication_version.Bill_Metadata["OfficialTitle"],
            aanhef=self._publication_version.Bill_Compact["Preamble"],
            wijzig_artikel=Artikel(
                label="Artikel",
                inhoud=self._publication_version.Bill_Compact["AmendmentArticle"],
            ),
            tekst_artikelen=[],
            tijd_artikel=Artikel(
                label="Artikel",
                inhoud=self._publication_version.Bill_Compact["TimeArticle"],
            ),
            sluiting=self._publication_version.Bill_Compact["Closing"],
            ondertekening=self._publication_version.Bill_Compact["Signed"],
            rechtsgebieden=self._as_dso_rechtsgebieden(self._publication_version.Bill_Metadata["Jurisdictions"]),
            onderwerpen=self._as_dso_onderwerpen(self._publication_version.Bill_Metadata["Subjects"]),
            soort_procedure=self._publication_version.Procedure_Type,
        )
        return besluit

    def _get_regeling(self) -> Regeling:
        regeling = Regeling(
            versienummer=self._act_frbr.Expression_Version,
            officiele_titel=self._publication_version.Act_Metadata["OfficialTitle"],
            citeertitel=self._publication_version.Act_Metadata["QuoteTitle"],
            # @todo: This might change when we add "Ontwerpen"
            is_officieel="true",
            rechtsgebieden=self._as_dso_rechtsgebieden(self._publication_version.Act_Metadata["Jurisdictions"]),
            onderwerpen=self._as_dso_onderwerpen(self._publication_version.Act_Metadata["Subjects"]),
        )
        return regeling

    def _get_procedure_verloop(self) -> dso_models.ProcedureVerloop:
        steps: List[dso_models.ProcedureStap] = []

        enactment_date: Optional[str] = self._publication_version.Procedural.get("EnactmentDate", None)
        if enactment_date is not None:
            steps.append(dso_models.ProcedureStap(
                soort_stap="Vaststelling",
                voltooid_op=enactment_date,
            ))

        signed_date: Optional[str] = self._publication_version.Procedural.get("SignedDate", None)
        if signed_date is None:
            raise RuntimeError("EnactmentDate.SignedDate is required")

        steps.append(dso_models.ProcedureStap(
            soort_stap="Ondertekening",
            voltooid_op=signed_date,
        ))

        procedure_verloop = dso_models.ProcedureVerloop(
            # @todo: This should be its own date
            bekend_op=self._publication_version.Announcement_Date.strftime('%Y-%m-%d'),
            stappen=steps,
        )
        return procedure_verloop

    def _get_resources(self) -> Resources:
        resources = Resources(
            policy_object_repository=self._get_policy_object_repository(),
            asset_repository=self._get_asset_repository(),
            werkingsgebied_repository=self._get_werkingsgebied_repository(),
        )
        return resources

    def _get_policy_object_repository(self) -> PolicyObjectRepository:
        repository = PolicyObjectRepository()
        for o in self._publication_data.objects:
            repository.add(o["Code"], o)
        return repository

    def _get_asset_repository(self) -> DSOAssetRepository:
        repository = DSOAssetRepository()
        for a in self._publication_data.assets:
            repository.add(a)
        return repository

    def _get_werkingsgebied_repository(self) -> WerkingsgebiedRepository:
        repository = WerkingsgebiedRepository(
            self._environment.Province_ID,
            self._act_frbr.Expression_Language,
        )
        for w in self._publication_data.werkingsgebieden:
            repository.add(w)
        return repository

    def _get_object_template_repository(self) -> ObjectTemplateRepository:
        repository = ObjectTemplateRepository(self._template.Object_Templates)
        return repository

    def _get_ambtsgebied(self) -> dict:
        return self._publication_data.area_of_juristiction

    def _get_soort_bestuursorgaan(self) -> str:
        bestuursorgaan: str = Bestuursorgaan[self._environment.Governing_Body_Type].value
        return bestuursorgaan

    def _as_dso_onderwerpen(self, values: List[str]) -> List[str]:
        result: List[str] = []
        for value in values:
            result.append(
                Onderwerp[value]
            )
        return result

    def _as_dso_rechtsgebieden(self, values: List[str]) -> List[str]:
        result: List[str] = []
        for value in values:
            result.append(
                Rechtsgebied[value]
            )
        return result
        

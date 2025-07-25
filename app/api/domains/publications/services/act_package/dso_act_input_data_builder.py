import uuid
from datetime import date, datetime
from typing import Dict, List, Optional

import dso.models as dso_models
from dso.act_builder.state_manager.input_data.ambtsgebied import Ambtsgebied
from dso.act_builder.state_manager.input_data.besluit import Artikel, Besluit, Bijlage, Motivering, WijzigBijlage
from dso.act_builder.state_manager.input_data.input_data_loader import InputData
from dso.act_builder.state_manager.input_data.object_template_repository import ObjectTemplateRepository
from dso.act_builder.state_manager.input_data.regeling import Regeling
from dso.act_builder.state_manager.input_data.resource.asset.asset_repository import (
    AssetRepository as DSOAssetRepository,
)
from dso.act_builder.state_manager.input_data.resource.besluit_pdf.besluit_pdf_repository import BesluitPdfRepository
from dso.act_builder.state_manager.input_data.resource.document.document_repository import DocumentRepository
from dso.act_builder.state_manager.input_data.resource.policy_object.policy_object_repository import (
    PolicyObjectRepository,
)
from dso.act_builder.state_manager.input_data.resource.resources import Resources
from dso.act_builder.state_manager.input_data.resource.werkingsgebied.werkingsgebied_repository import (
    WerkingsgebiedRepository,
)

from app.api.domains.publications.types.api_input_data import (
    ActFrbr,
    ActMutation,
    ApiActInputData,
    BillFrbr,
    OwData,
    PublicationData,
    Purpose,
)
from app.api.domains.publications.types.enums import DocumentType, MutationStrategy, PackageType, ProcedureType
from app.api.domains.publications.types.waardelijsten import Bestuursorgaan, Onderwerp, Rechtsgebied
from app.core.settings import KoopSettings
from app.core.tables.publications import (
    PublicationActTable,
    PublicationEnvironmentTable,
    PublicationTable,
    PublicationTemplateTable,
    PublicationVersionTable,
)

DOCUMENT_TYPE_MAP = {
    DocumentType.VISION: "OMGEVINGSVISIE",
    DocumentType.PROGRAM: "PROGRAMMA",
}

OPDRACHT_TYPE_MAP = {
    PackageType.VALIDATION: "VALIDATIE",
    PackageType.PUBLICATION: "PUBLICATIE",
}

PROCEDURE_TYPE_MAP = {
    ProcedureType.DRAFT: "Ontwerpbesluit",
    ProcedureType.FINAL: "Definitief_besluit",
}

DUTCH_MONTHS = {
    1: "januari",
    2: "februari",
    3: "maart",
    4: "april",
    5: "mei",
    6: "juni",
    7: "juli",
    8: "augustus",
    9: "september",
    10: "oktober",
    11: "november",
    12: "december",
}


class DsoActInputDataBuilder:
    def __init__(self, koop_settings: Dict[str, KoopSettings], api_input_data: ApiActInputData):
        self._koop_settings: Dict[str, KoopSettings] = koop_settings
        self._publication_version: PublicationVersionTable = api_input_data.Publication_Version
        self._package_type: PackageType = api_input_data.Package_Type
        self._bill_frbr: BillFrbr = api_input_data.Bill_Frbr
        self._act_frbr: ActFrbr = api_input_data.Act_Frbr
        self._consolidation_purpose: Purpose = api_input_data.Consolidation_Purpose
        self._publication_data: PublicationData = api_input_data.Publication_Data
        self._publication: PublicationTable = api_input_data.Publication_Version.Publication
        self._environment: PublicationEnvironmentTable = api_input_data.Publication_Version.Publication.Environment
        self._act: PublicationActTable = api_input_data.Publication_Version.Publication.Act
        self._template: PublicationTemplateTable = self._publication.Template
        self._act_mutation: Optional[ActMutation] = api_input_data.Act_Mutation
        self._ow_data: OwData = api_input_data.Ow_Data
        self._mutation_strategy: MutationStrategy = api_input_data.Mutation_Strategy

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
            regeling_mutatie=self._get_regeling_mutatie(),
            ow_data=self._get_ow_data(),
        )
        return input_data

    def _get_publication_settings(self) -> dso_models.PublicationSettings:
        dso_document_type: str = DOCUMENT_TYPE_MAP[self._publication.Document_Type]
        dso_opdracht_type: str = OPDRACHT_TYPE_MAP[self._package_type]

        publication_settings = dso_models.PublicationSettings(
            document_type=dso_document_type,
            datum_bekendmaking=self._publication_version.Announcement_Date.strftime("%Y-%m-%d"),
            provincie_id=self._environment.Province_ID,
            soort_bestuursorgaan=self._get_soort_bestuursorgaan(),
            regeling_componentnaam=self._get_componentnaam(),
            provincie_ref=f"/tooi/id/provincie/{self._environment.Province_ID}",
            opdracht={
                "opdracht_type": dso_opdracht_type,
                "id_levering": str(uuid.uuid4()),
                "id_bevoegdgezag": self._environment.Authority_ID,
                "id_aanleveraar": self._environment.Submitter_ID,
                "publicatie_bestand": self._get_akn_filename(),
                "datum_bekendmaking": self._publication_version.Announcement_Date.strftime("%Y-%m-%d"),
            },
            instelling_doel=self._get_instelling_doel(),
            besluit_frbr=dso_models.BillFRBR(
                Work_Province_ID=self._environment.Province_ID,
                Work_Country=self._bill_frbr.Work_Country,
                Work_Date=self._bill_frbr.Work_Date,
                Work_Other=self._bill_frbr.Work_Other,
                Expression_Language=self._bill_frbr.Expression_Language,
                Expression_Date=self._bill_frbr.Expression_Date,
                Expression_Version=self._bill_frbr.Expression_Version,
            ),
            regeling_frbr=dso_models.ActFRBR(
                Work_Province_ID=self._environment.Province_ID,
                Work_Country=self._act_frbr.Work_Country,
                Work_Date=self._act_frbr.Work_Date,
                Work_Other=self._act_frbr.Work_Other,
                Expression_Language=self._act_frbr.Expression_Language,
                Expression_Date=self._act_frbr.Expression_Date,
                Expression_Version=self._act_frbr.Expression_Version,
            ),
            intrekking=None,
        )
        return publication_settings

    def _get_akn_filename(self) -> str:
        package_type: str = (self._package_type[:3]).lower()
        filename: str = f"akn_nl_bill_{self._environment.Province_ID}-{package_type}-{self._bill_frbr.Work_Date}-{self._bill_frbr.Work_Other}-{self._bill_frbr.Expression_Version}.xml"
        return filename

    def _get_besluit(self) -> Besluit:
        dso_procedure_type: str = PROCEDURE_TYPE_MAP[self._publication.Procedure_Type]

        besluit = Besluit(
            officiele_titel=self._publication_version.Bill_Metadata["Official_Title"],
            citeertitel=self._publication_version.Bill_Metadata["Quote_Title"],
            aanhef=self._publication_version.Bill_Compact["Preamble"],
            wijzig_artikel=self._get_wijzigingsartikel(),
            wijzig_bijlage=self._get_amendment_appendix(),
            tekst_artikelen=self._get_text_articles(),
            tijd_artikel=self._get_time_article(),
            sluiting=self._get_closing_text(),
            ondertekening=self._publication_version.Bill_Compact["Signed"],
            rechtsgebieden=self._as_dso_rechtsgebieden(self._publication_version.Bill_Metadata["Jurisdictions"]),
            onderwerpen=self._as_dso_onderwerpen(self._publication_version.Bill_Metadata["Subjects"]),
            soort_procedure=dso_procedure_type,
            bijlagen=self._get_appendices(),
            motivering=self._get_motivering(),
        )
        return besluit

    def _get_regeling(self) -> Regeling:
        regeling = Regeling(
            versienummer=str(self._act_frbr.Expression_Version),
            officiele_titel=self._act.Metadata["Official_Title"],
            citeertitel=self._act.Metadata["Quote_Title"],
            is_officieel=("true" if self._publication.Procedure_Type == ProcedureType.FINAL else "false"),
            rechtsgebieden=self._as_dso_rechtsgebieden(self._act.Metadata["Jurisdictions"]),
            onderwerpen=self._as_dso_onderwerpen(self._act.Metadata["Subjects"]),
        )
        return regeling

    def _get_instelling_doel(self) -> dso_models.InstellingDoel:
        frbr = dso_models.DoelFRBR(
            Work_Province_ID=self._consolidation_purpose.Work_Province_ID,
            Work_Date=self._consolidation_purpose.Work_Date,
            Work_Other=self._consolidation_purpose.Work_Other,
        )

        datum: Optional[str] = None
        if self._publication.Procedure_Type == ProcedureType.FINAL.value:
            datum = self._publication_version.Effective_Date.strftime("%Y-%m-%d")

        result = dso_models.InstellingDoel(
            frbr=frbr,
            datum_juridisch_werkend_vanaf=datum,
        )
        return result

    def _get_time_article(self) -> Optional[Artikel]:
        result = Artikel(
            nummer="II",
            inhoud=self._get_time_article_content(),
        )
        return result

    def _get_procedure_verloop(self) -> dso_models.ProcedureVerloop:
        steps: List[dso_models.ProcedureStap] = []

        enactment_date: Optional[str] = self._publication_version.Procedural.get("Enactment_Date", None)
        if enactment_date is not None:
            steps.append(
                dso_models.ProcedureStap(
                    soort_stap="Vaststelling",
                    voltooid_op=enactment_date,
                )
            )

        signed_date: Optional[str] = self._publication_version.Procedural.get("Signed_Date", None)
        if signed_date is not None:
            steps.append(
                dso_models.ProcedureStap(
                    soort_stap="Ondertekening",
                    voltooid_op=signed_date,
                )
            )

        procedure_verloop = dso_models.ProcedureVerloop(
            # @todo: This should be its own date
            bekend_op=self._publication_version.Procedural["Procedural_Announcement_Date"],
            stappen=steps,
        )
        return procedure_verloop

    def _get_wijzigingsartikel(self) -> str:
        text: str = self._publication_version.Bill_Compact["Amendment_Article"]

        enactment_date: Optional[str] = self._publication_version.Procedural.get("Enactment_Date", None)
        if enactment_date is not None:
            date_readable: str = self._get_readable_date_from_str(enactment_date)
            text = text.replace("[[ENACTMENT_DATE]]", date_readable)

        result = Artikel(
            nummer="I",
            inhoud=text,
        )
        return result

    def _get_amendment_appendix(self) -> WijzigBijlage:
        data: dict = self._publication_version.Bill_Compact.get("Amendment_Appendix", {})
        number = data.get("Number", "A")
        title = data.get("Title", "bij Artikel I")

        result = WijzigBijlage(
            nummer=number,
            opschrift=title,
        )
        return result

    def _get_text_articles(self) -> List[Artikel]:
        result: List[Artikel] = []
        for custom_article in self._publication_version.Bill_Compact.get("Custom_Articles", []):
            article: Artikel = Artikel(
                nummer=custom_article["Number"],
                inhoud=custom_article["Content"],
            )
            result.append(article)
        return result

    def _get_appendices(self) -> List[Bijlage]:
        appendices: List[dict] = self._publication_version.Bill_Compact.get("Appendices", [])
        result: List[dict] = []

        for appendix in appendices:
            bijlage = Bijlage(
                nummer=appendix["Number"],
                opschrift=appendix["Title"],
                content=appendix["Content"],
            )
            result.append(bijlage)
        return result

    def _get_motivering(self) -> Optional[Motivering]:
        motivation: Optional[dict] = self._publication_version.Bill_Compact.get("Motivation", None)
        if motivation is None:
            return None

        appendices: List[Bijlage] = []
        for appendix in motivation.get("Appendices", []):
            bijlage = Bijlage(
                nummer=appendix["Number"],
                opschrift=appendix["Title"],
                content=appendix["Content"],
            )
            appendices.append(bijlage)

        result = Motivering(
            nummer=motivation.get("Number"),
            opschrift=motivation["Title"],
            content=motivation["Content"],
            bijlagen=appendices,
        )
        return result

    def _get_resources(self) -> Resources:
        resources = Resources(
            policy_object_repository=self._get_policy_object_repository(),
            asset_repository=self._get_asset_repository(),
            werkingsgebied_repository=self._get_werkingsgebied_repository(),
            besluit_pdf_repository=self._get_pdf_repository(),
            document_repository=self._get_document_repository(),
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
        repository = WerkingsgebiedRepository()
        for w in self._publication_data.werkingsgebieden:
            repository.add(w)
        return repository

    def _get_pdf_repository(self) -> BesluitPdfRepository:
        repository = BesluitPdfRepository()
        for a in self._publication_data.bill_attachments:
            repository.add(a)
        return repository

    def _get_document_repository(self) -> DocumentRepository:
        repository = DocumentRepository()
        for b in self._publication_data.documents:
            repository.add(b)
        return repository

    def _get_object_template_repository(self) -> ObjectTemplateRepository:
        repository = ObjectTemplateRepository(self._template.Object_Templates)
        return repository

    def _get_ambtsgebied(self) -> Ambtsgebied:
        aoj: dict = self._publication_data.area_of_jurisdiction
        ambtsgebied: Ambtsgebied = Ambtsgebied(
            UUID=aoj["UUID"],
            identificatie_suffix=aoj["Administrative_Borders_ID"],
            domein=aoj["Administrative_Borders_Domain"],
            geldig_op=aoj["Administrative_Borders_Date"].strftime("%Y-%m-%d"),
            titel=aoj["Title"],
        )
        return ambtsgebied

    def _get_soort_bestuursorgaan(self) -> str:
        bestuursorgaan: str = Bestuursorgaan[self._environment.Governing_Body_Type].value
        return bestuursorgaan

    def _as_dso_onderwerpen(self, values: List[str]) -> List[str]:
        result: List[str] = []
        for value in values:
            result.append(Onderwerp[value])
        return result

    def _as_dso_rechtsgebieden(self, values: List[str]) -> List[str]:
        result: List[str] = []
        for value in values:
            result.append(Rechtsgebied[value])
        return result

    def _get_closing_text(self) -> str:
        text: str = self._publication_version.Bill_Compact["Closing"]

        signed_date: Optional[str] = self._publication_version.Procedural.get("Signed_Date", None)
        if signed_date is not None:
            signed_date_readable: str = self._get_readable_date_from_str(signed_date)
            text = text.replace("[[SIGNED_DATE]]", signed_date_readable)

        return text

    def _get_time_article_content(self) -> str:
        text: str = self._publication_version.Bill_Compact.get("Time_Article", "")

        if self._publication_version.Effective_Date is not None:
            effective_date_readable: str = self._get_readable_date(self._publication_version.Effective_Date)
            text = text.replace("[[EFFECTIVE_DATE]]", effective_date_readable)

        return text

    def _get_readable_date(self, d: date) -> str:
        formatted_date = f"{d.day} {DUTCH_MONTHS[d.month]} {d.year}"
        return formatted_date

    def _get_readable_date_from_str(self, date_str: str) -> str:
        d: date = datetime.strptime(date_str, "%Y-%m-%d")
        result: str = self._get_readable_date(d)
        return result

    def _get_regeling_mutatie(self) -> Optional[dso_models.RegelingMutatie]:
        if self._act_mutation is None:
            return None

        if self._environment.Code is None:
            raise RuntimeError("Expecting Environment.Code to be set")

        renvooi: Optional[KoopSettings] = self._koop_settings.get(self._environment.Code)
        if renvooi is None:
            raise RuntimeError("Missing runtime environment settings for this PublicationEnvironment")

        frbr = dso_models.ActFRBR(
            Work_Province_ID=self._act_mutation.Consolidated_Act_Frbr.Work_Province_ID,
            Work_Country=self._act_mutation.Consolidated_Act_Frbr.Work_Country,
            Work_Date=self._act_mutation.Consolidated_Act_Frbr.Work_Date,
            Work_Other=self._act_mutation.Consolidated_Act_Frbr.Work_Other,
            Expression_Language=self._act_mutation.Consolidated_Act_Frbr.Expression_Language,
            Expression_Date=self._act_mutation.Consolidated_Act_Frbr.Expression_Date,
            Expression_Version=self._act_mutation.Consolidated_Act_Frbr.Expression_Version,
        )

        te_verwijderden_werkingsgebieden = [
            dso_models.VerwijderdWerkingsgebied(
                UUID=w["UUID"],
                code=w["Code"],
                object_id=w["Object_ID"],
                frbr=dso_models.GioFRBR.model_validate(w["Frbr"]),
                geboorteregeling=w["Owner_Act"],
                titel=w["Title"],
            )
            for w in self._act_mutation.Removed_Werkingsgebieden
        ]

        match self._mutation_strategy:
            case MutationStrategy.REPLACE:
                result = dso_models.VervangRegelingMutatie(
                    was_regeling_frbr=frbr,
                    bekend_wid_map=self._act_mutation.Known_Wid_Map,
                    bekend_wids=self._act_mutation.Known_Wids,
                    te_verwijderden_werkingsgebieden=te_verwijderden_werkingsgebieden,
                )
                return result

            case MutationStrategy.RENVOOI:
                result = dso_models.RenvooiRegelingMutatie(
                    was_regeling_frbr=frbr,
                    was_regeling_vrijetekst=self._act_mutation.Consolidated_Act_Text,
                    bekend_wid_map=self._act_mutation.Known_Wid_Map,
                    bekend_wids=self._act_mutation.Known_Wids,
                    te_verwijderden_werkingsgebieden=te_verwijderden_werkingsgebieden,
                    renvooi_api_key=renvooi.API_KEY,
                    renvooi_api_url=renvooi.RENVOOI_API_URL,
                )
                return result

            case _:
                raise NotImplementedError()

    def _get_componentnaam(self) -> str:
        if self._act_mutation is None:
            return "nieuweregeling"

        key: str = "_".join(
            [
                str(self._act_frbr.Work_Province_ID),
                str(self._act_frbr.Work_Other),
                str(self._act_frbr.Expression_Version),
                str(self._act_mutation.Consolidated_Act_Frbr.Expression_Version),
            ]
        ).replace("-", "_")
        return key

    def _get_ow_data(self) -> dso_models.OwData:
        # @todo
        ow_data_dict = self._ow_data.__dict__
        result = dso_models.OwData.from_dict(ow_data_dict)
        return result

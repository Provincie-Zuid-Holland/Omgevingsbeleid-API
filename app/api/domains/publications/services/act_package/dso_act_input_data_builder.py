import uuid
from datetime import date, datetime

import dso.act_builder.state_manager.input_data.resource.gebieden as dso_gebieden
import dso.models as dso_models
from dso.act_builder.services.ow.state.ow_state import OwState
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
from dso.models import DocumentType as DSODocumentType
from dso.models import OpdrachtType
from dso.services.koop.waardelijsten.gen import (
    BestuursorgaanType,
    OnderwerpType,
    ProcedureStappen,
    RechtsgebiedType,
)
from dso.services.koop.waardelijsten.gen import (
    ProcedureType as DSOProcedureType,
)

from app.api.domains.publications.types.api_input_data import (
    ActFrbr,
    ActMutation,
    ApiActInputData,
    BillFrbr,
    PublicationData,
    Purpose,
)
from app.api.domains.publications.types.enums import (
    DocumentType as APIDocumentType,
)
from app.api.domains.publications.types.enums import (
    MutationStrategy,
    PackageType,
)
from app.api.domains.publications.types.enums import (
    ProcedureType as APIProcedureType,
)
from app.core.settings import KoopSettings
from app.core.tables.publications import (
    PublicationActTable,
    PublicationEnvironmentTable,
    PublicationTable,
    PublicationTemplateTable,
    PublicationVersionTable,
)

DOCUMENT_TYPE_MAP: dict[str, DSODocumentType] = {
    APIDocumentType.VISION.value: DSODocumentType.OMGEVINGSVISIE,
    APIDocumentType.PROGRAM.value: DSODocumentType.PROGRAMMA,
}

OPDRACHT_TYPE_MAP: dict[PackageType, OpdrachtType] = {
    PackageType.VALIDATION: OpdrachtType.VALIDATIE,
    PackageType.PUBLICATION: OpdrachtType.PUBLICATIE,
}

PROCEDURE_TYPE_MAP: dict[APIProcedureType, DSOProcedureType] = {
    APIProcedureType.DRAFT: DSOProcedureType.ontwerpbesluit,
    APIProcedureType.FINAL: DSOProcedureType.definitief_besluit,
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
    def __init__(
        self,
        koop_settings: dict[str, KoopSettings],
        ow_dataset: str,
        ow_gebied: str,
        api_input_data: ApiActInputData,
    ):
        self._koop_settings: dict[str, KoopSettings] = koop_settings
        self._ow_dataset: str = ow_dataset
        self._ow_gebied: str = ow_gebied
        self._publication_version: PublicationVersionTable = api_input_data.publication_version
        self._package_type: PackageType = api_input_data.package_type
        self._bill_frbr: BillFrbr = api_input_data.bill_frbr
        self._act_frbr: ActFrbr = api_input_data.act_frbr
        self._consolidation_purpose: Purpose = api_input_data.consolidation_purpose
        self._publication_data: PublicationData = api_input_data.publication_data
        self._publication: PublicationTable = api_input_data.publication_version.publication
        self._environment: PublicationEnvironmentTable = api_input_data.publication_version.publication.environment
        self._act: PublicationActTable = api_input_data.publication_version.publication.act
        self._template: PublicationTemplateTable = self._publication.template
        self._act_mutation: ActMutation | None = api_input_data.act_mutation
        self._mutation_strategy: MutationStrategy = api_input_data.mutation_strategy
        self._ow_state_json: str | None = api_input_data.ow_state

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
            ow_state=self._get_ow_state(),
            ow_dataset=self._ow_dataset,
            ow_gebied=self._ow_gebied,
        )
        return input_data

    def _get_publication_settings(self) -> dso_models.PublicationSettings:
        dso_document_type: DSODocumentType = DOCUMENT_TYPE_MAP[self._publication.document_type]
        dso_opdracht_type: OpdrachtType = OPDRACHT_TYPE_MAP[self._package_type]

        publication_settings = dso_models.PublicationSettings(
            document_type=dso_document_type,
            datum_bekendmaking=self._publication_version.announcement_date.strftime("%Y-%m-%d"),
            provincie_id=self._environment.province_id,
            soort_bestuursorgaan=self._get_soort_bestuursorgaan(),
            regeling_componentnaam=self._get_componentnaam(),
            provincie_ref=f"/tooi/id/provincie/{self._environment.province_id}",
            opdracht=dso_models.PublicatieOpdracht(
                opdracht_type=dso_opdracht_type,
                id_levering=str(uuid.uuid4()),
                id_bevoegdgezag=self._environment.authority_id,
                id_aanleveraar=self._environment.submitter_id,
                publicatie_bestand=self._get_akn_filename(),
                datum_bekendmaking=self._publication_version.announcement_date.strftime("%Y-%m-%d"),
            ).model_dump(),
            instelling_doel=self._get_instelling_doel(),
            besluit_frbr=dso_models.BillFRBR(
                work_province_id=self._environment.province_id,
                work_country=self._bill_frbr.work_country,
                work_date=self._bill_frbr.work_date,
                work_other=self._bill_frbr.work_other,
                expression_language=self._bill_frbr.expression_language,
                expression_date=self._bill_frbr.expression_date,
                expression_version=self._bill_frbr.expression_version,
            ),
            regeling_frbr=dso_models.ActFRBR(
                work_province_id=self._environment.province_id,
                work_country=self._act_frbr.work_country,
                work_date=self._act_frbr.work_date,
                work_other=self._act_frbr.work_other,
                expression_language=self._act_frbr.expression_language,
                expression_date=self._act_frbr.expression_date,
                expression_version=self._act_frbr.expression_version,
            ),
            intrekking=None,
        )
        return publication_settings

    def _get_akn_filename(self) -> str:
        package_type: str = (self._package_type[:3]).lower()
        filename: str = f"akn_nl_bill_{self._environment.province_id}-{package_type}-{self._bill_frbr.work_date}-{self._bill_frbr.work_other}-{self._bill_frbr.expression_version}.xml"
        return filename

    def _get_besluit(self) -> Besluit:
        api_procedure_type: APIProcedureType = APIProcedureType(self._publication.procedure_type)
        dso_procedure_type: DSOProcedureType = PROCEDURE_TYPE_MAP[api_procedure_type]

        besluit = Besluit(
            officiele_titel=self._publication_version.bill_metadata["official_title"],
            citeertitel=self._publication_version.bill_metadata["quote_title"],
            aanhef=self._publication_version.bill_compact["preamble"],
            wijzig_artikel=self._get_wijzigingsartikel(),
            wijzig_bijlage=self._get_amendment_appendix(),
            tekst_artikelen=self._get_text_articles(),
            tijd_artikel=self._get_time_article(),
            sluiting=self._get_closing_text(),
            ondertekening=self._publication_version.bill_compact.get("signed", ""),
            rechtsgebieden=self._as_dso_rechtsgebieden(self._publication_version.bill_metadata["jurisdictions"]),
            onderwerpen=self._as_dso_onderwerpen(self._publication_version.bill_metadata["subjects"]),
            soort_procedure=dso_procedure_type,
            bijlagen=self._get_appendices(),
            motivering=self._get_motivering(),
        )
        return besluit

    def _get_regeling(self) -> Regeling:
        regeling = Regeling(
            versienummer=str(self._act_frbr.expression_version),
            officiele_titel=self._act.meta_data["official_title"],
            citeertitel=self._act.meta_data["quote_title"],
            is_officieel=("true" if self._publication.procedure_type == APIProcedureType.FINAL else "false"),
            rechtsgebieden=self._as_dso_rechtsgebieden(self._act.meta_data["jurisdictions"]),
            onderwerpen=self._as_dso_onderwerpen(self._act.meta_data["subjects"]),
        )
        return regeling

    def _get_instelling_doel(self) -> dso_models.InstellingDoel:
        frbr = dso_models.DoelFRBR(
            work_province_id=self._consolidation_purpose.work_province_id,
            work_date=self._consolidation_purpose.work_date,
            work_other=self._consolidation_purpose.work_other,
        )

        datum: str | None = None
        if self._publication.procedure_type == APIProcedureType.FINAL.value:
            datum = self._publication_version.effective_date.strftime("%Y-%m-%d")

        result = dso_models.InstellingDoel(
            frbr=frbr,
            datum_juridisch_werkend_vanaf=datum,
        )
        return result

    def _get_time_article(self) -> Artikel | None:
        result = Artikel(
            nummer="II",
            inhoud=self._get_time_article_content(),
        )
        return result

    def _get_procedure_verloop(self) -> dso_models.ProcedureVerloop:
        steps: list[dso_models.ProcedureStap] = []

        enactment_date: str | None = self._publication_version.procedural.get("enactment_date", None)
        if enactment_date is not None:
            steps.append(
                dso_models.ProcedureStap(
                    soort_stap=ProcedureStappen.vaststelling,
                    voltooid_op=enactment_date,
                )
            )

        signed_date: str | None = self._publication_version.procedural.get("signed_date", None)
        if signed_date is not None:
            steps.append(
                dso_models.ProcedureStap(
                    soort_stap=ProcedureStappen.ondertekening,
                    voltooid_op=signed_date,
                )
            )

        procedure_verloop = dso_models.ProcedureVerloop(
            # @todo: This should be its own date
            bekend_op=self._publication_version.procedural["procedural_announcement_date"],
            stappen=steps,
        )
        return procedure_verloop

    def _get_wijzigingsartikel(self) -> Artikel:
        text: str = self._publication_version.bill_compact["amendment_article"]

        enactment_date: str | None = self._publication_version.procedural.get("enactment_date", None)
        if enactment_date is not None:
            date_readable: str = self._get_readable_date_from_str(enactment_date)
            text = text.replace("[[ENACTMENT_DATE]]", date_readable)

        result = Artikel(
            nummer="I",
            inhoud=text,
        )
        return result

    def _get_amendment_appendix(self) -> WijzigBijlage:
        data: dict = self._publication_version.bill_compact.get("amendment_appendix", {})
        number = data.get("number", "A")
        title = data.get("title", "bij Artikel I")

        result = WijzigBijlage(
            nummer=number,
            opschrift=title,
        )
        return result

    def _get_text_articles(self) -> list[Artikel]:
        result: list[Artikel] = []
        for custom_article in self._publication_version.bill_compact.get("custom_articles", []):
            article: Artikel = Artikel(
                nummer=custom_article["number"],
                inhoud=custom_article["content"],
            )
            result.append(article)
        return result

    def _get_appendices(self) -> list[Bijlage]:
        appendices: list[dict] = self._publication_version.bill_compact.get("appendices", [])
        result: list[Bijlage] = []

        for appendix in appendices:
            bijlage = Bijlage(
                nummer=appendix["number"],
                opschrift=appendix["title"],
                content=appendix["content"],
            )
            result.append(bijlage)
        return result

    def _get_motivering(self) -> Motivering | None:
        motivation: dict | None = self._publication_version.bill_compact.get("motivation", None)
        if motivation is None:
            return None

        appendices: list[Bijlage] = []
        for appendix in motivation.get("appendices", []):
            bijlage = Bijlage(
                nummer=appendix["number"],
                opschrift=appendix["title"],
                content=appendix["content"],
            )
            appendices.append(bijlage)

        result = Motivering(
            nummer=motivation.get("number"),
            opschrift=motivation["title"],
            content=motivation["content"],
            bijlagen=appendices,
        )
        return result

    def _get_resources(self) -> Resources:
        resources = Resources(
            policy_object_repository=self._get_policy_object_repository(),
            asset_repository=self._get_asset_repository(),
            gio_repository=self._get_gio_repository(),
            gebiedengroep_repository=self._get_gebiedengroep_repository(),
            gebiedsaanwijzingen_repository=self._get_gebiedsaanwijzingen_repository(),
            besluit_pdf_repository=self._get_pdf_repository(),
            document_repository=self._get_document_repository(),
        )
        return resources

    def _get_policy_object_repository(self) -> PolicyObjectRepository:
        repository = PolicyObjectRepository()
        for o in self._publication_data.used_objects:
            repository.add(o["code"], o)
        return repository

    def _get_asset_repository(self) -> DSOAssetRepository:
        repository = DSOAssetRepository()
        for a in self._publication_data.assets:
            repository.add(a)
        return repository

    def _get_gio_repository(self) -> dso_gebieden.GioRepository:
        repository = dso_gebieden.GioRepository()
        for input_gio in self._publication_data.gios.values():
            locaties: list[dso_gebieden.GioLocatie] = [
                dso_gebieden.GioLocatie(
                    code=input_locatie.code,
                    title=input_locatie.title,
                    basisgeo_id=input_locatie.basisgeo_id,
                    gml=input_locatie.gml,
                )
                for input_locatie in input_gio.locaties
            ]
            repository.add(
                dso_gebieden.Gio(
                    key=input_gio.key,
                    source_codes=input_gio.source_codes,
                    title=input_gio.title,
                    frbr=dso_models.GioFRBR.model_validate(input_gio.frbr.model_dump()),
                    new=input_gio.new,
                    geboorteregeling=input_gio.geboorteregeling,
                    achtergrond_verwijzing=input_gio.achtergrond_verwijzing,
                    achtergrond_actualiteit=input_gio.achtergrond_actualiteit,
                    locaties=locaties,
                )
            )
        return repository

    def _get_gebiedengroep_repository(self) -> dso_gebieden.GebiedengroepRepository:
        repository = dso_gebieden.GebiedengroepRepository()
        for input_groep in self._publication_data.gebiedengroepen.values():
            repository.add(
                dso_gebieden.GebiedenGroep(
                    id=uuid.UUID(input_groep.id),
                    code=input_groep.code,
                    title=input_groep.title,
                    gio_key=input_groep.gio_key,
                )
            )
        return repository

    def _get_gebiedsaanwijzingen_repository(self) -> dso_gebieden.GebiedsaanwijzingRepository:
        repository = dso_gebieden.GebiedsaanwijzingRepository()
        for input_aanwijzing in self._publication_data.gebiedsaanwijzingen.values():
            repository.add(
                dso_gebieden.Gebiedsaanwijzing(
                    id=uuid.UUID(input_aanwijzing.id),
                    code=input_aanwijzing.code,
                    aanwijzing_type=input_aanwijzing.aanwijzing_type,
                    aanwijzing_groep=input_aanwijzing.aanwijzing_group,
                    title=input_aanwijzing.title,
                    gebied_codes=input_aanwijzing.resolved_gebied_codes,
                    gio_key=input_aanwijzing.gio_key,
                )
            )
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
        repository = ObjectTemplateRepository(self._template.object_templates)
        return repository

    def _get_ambtsgebied(self) -> Ambtsgebied:
        aoj: dict = self._publication_data.area_of_jurisdiction
        ambtsgebied: Ambtsgebied = Ambtsgebied(
            id=aoj["id"],
            identificatie_suffix=aoj["administrative_borders_id"],
            domein=aoj["administrative_borders_domain"],
            geldig_op=aoj["administrative_borders_date"].strftime("%Y-%m-%d"),
            titel=aoj["title"],
        )
        return ambtsgebied

    def _get_soort_bestuursorgaan(self) -> BestuursorgaanType:
        bestuursorgaan: BestuursorgaanType = BestuursorgaanType[self._environment.governing_body_type]
        return bestuursorgaan

    def _as_dso_onderwerpen(self, values: list[str]) -> list[OnderwerpType]:
        result: list[OnderwerpType] = []
        for value in values:
            result.append(OnderwerpType[value])
        return result

    def _as_dso_rechtsgebieden(self, values: list[str]) -> list[RechtsgebiedType]:
        result: list[RechtsgebiedType] = []
        for value in values:
            result.append(RechtsgebiedType[value])
        return result

    def _get_closing_text(self) -> str:
        text: str = self._publication_version.bill_compact.get("closing", "")
        if text == "":
            return text

        signed_date: str | None = self._publication_version.procedural.get("signed_date", None)
        if signed_date is not None:
            signed_date_readable: str = self._get_readable_date_from_str(signed_date)
            text = text.replace("[[SIGNED_DATE]]", signed_date_readable)

        return text

    def _get_time_article_content(self) -> str:
        text: str = self._publication_version.bill_compact.get("time_article", "")

        if self._publication_version.effective_date is not None:
            effective_date_readable: str = self._get_readable_date(self._publication_version.effective_date)
            text = text.replace("[[EFFECTIVE_DATE]]", effective_date_readable)

        return text

    def _get_readable_date(self, d: date) -> str:
        formatted_date = f"{d.day} {DUTCH_MONTHS[d.month]} {d.year}"
        return formatted_date

    def _get_readable_date_from_str(self, date_str: str) -> str:
        d: date = datetime.strptime(date_str, "%Y-%m-%d")
        result: str = self._get_readable_date(d)
        return result

    def _get_regeling_mutatie(self) -> dso_models.RegelingMutatie | None:
        if self._act_mutation is None:
            return None

        if self._environment.code is None:
            raise RuntimeError("Expecting Environment.code to be set")

        renvooi: KoopSettings | None = self._koop_settings.get(self._environment.code)
        if renvooi is None:
            raise RuntimeError("Missing runtime environment settings for this PublicationEnvironment")

        frbr = dso_models.ActFRBR(
            work_province_id=self._act_mutation.consolidated_act_frbr.work_province_id,
            work_country=self._act_mutation.consolidated_act_frbr.work_country,
            work_date=self._act_mutation.consolidated_act_frbr.work_date,
            work_other=self._act_mutation.consolidated_act_frbr.work_other,
            expression_language=self._act_mutation.consolidated_act_frbr.expression_language,
            expression_date=self._act_mutation.consolidated_act_frbr.expression_date,
            expression_version=self._act_mutation.consolidated_act_frbr.expression_version,
        )

        te_verwijderden_gios = [
            dso_models.VerwijderdeGio(
                frbr=dso_models.GioFRBR.model_validate(w["frbr"]),
            )
            for w in self._act_mutation.removed_gios
        ]

        match self._mutation_strategy:
            case MutationStrategy.REPLACE:
                result = dso_models.VervangRegelingMutatie(
                    was_regeling_frbr=frbr,
                    bekend_wid_map=self._act_mutation.known_wid_map,
                    bekend_wids=self._act_mutation.known_wids,
                    te_verwijderden_gios=te_verwijderden_gios,
                )
                return result

            case MutationStrategy.RENVOOI:
                result = dso_models.RenvooiRegelingMutatie(
                    was_regeling_frbr=frbr,
                    was_regeling_vrijetekst=self._act_mutation.consolidated_act_text,
                    bekend_wid_map=self._act_mutation.known_wid_map,
                    bekend_wids=self._act_mutation.known_wids,
                    te_verwijderden_gios=te_verwijderden_gios,
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
                str(self._act_frbr.work_province_id),
                str(self._act_frbr.work_other),
                str(self._act_frbr.expression_version),
                str(self._act_mutation.consolidated_act_frbr.expression_version),
            ]
        ).replace("-", "_")
        return key

    def _get_ow_state(self) -> OwState:
        if self._ow_state_json is None:
            return OwState()

        ow_state: OwState = OwState.model_validate_json(self._ow_state_json)
        return ow_state

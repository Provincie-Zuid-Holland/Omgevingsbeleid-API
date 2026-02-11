from datetime import datetime
from typing import List, Optional, Set

from app.api.domains.publications.services.act_package.publication_gebieden_provider import (
    GebiedenData,
    PublicationGebiedenProvider,
)
from app.api.domains.publications.services.act_package.publication_gebiedsaanwijzing_provider import (
    GebiedsaanwijzingData,
    PublicationGebiedsaanwijzingProvider,
)
from app.api.domains.publications.services.act_package.publication_gios_provider import (
    PublicationGeoData,
    PublicationGiosProviderFactory,
)
import dso.models as dso_models
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.api.domains.publications.repository.publication_aoj_repository import PublicationAOJRepository
from app.api.domains.publications.services.publication_object_provider import PublicationObjectProvider
from app.api.domains.publications.services.act_package.documents_provider import PublicationDocumentsProvider
from app.api.domains.publications.services.assets.publication_asset_provider import PublicationAssetProvider
from app.api.domains.publications.services.template_parser import TemplateParser
from app.api.domains.publications.services.validate_publication_service import (
    ValidatePublicationError,
    validation_exception,
)
from app.api.domains.publications.types.api_input_data import ActFrbr, BillFrbr, PublicationData
from app.core.tables.publications import PublicationAreaOfJurisdictionTable, PublicationVersionTable


class ActPublicationDataProvider:
    def __init__(
        self,
        publication_object_provider: PublicationObjectProvider,
        publication_asset_provider: PublicationAssetProvider,
        publication_gebiedsaanwijzingen_provider: PublicationGebiedsaanwijzingProvider,
        publication_gebieden_provider: PublicationGebiedenProvider,
        publication_gios_provider: PublicationGiosProviderFactory,
        publication_documents_provider: PublicationDocumentsProvider,
        publication_aoj_repository: PublicationAOJRepository,
        template_parser: TemplateParser,
    ):
        self._publication_object_provider: PublicationObjectProvider = publication_object_provider
        self._publication_asset_provider: PublicationAssetProvider = publication_asset_provider
        self._publication_asset_provider: PublicationAssetProvider = publication_asset_provider
        self._publication_gebiedsaanwijzingen_provider: PublicationGebiedsaanwijzingProvider = (
            publication_gebiedsaanwijzingen_provider
        )
        self._publication_gebieden_provider: PublicationGebiedenProvider = publication_gebieden_provider
        self._publication_gios_provider: PublicationGiosProviderFactory = publication_gios_provider
        self._publication_documents_provider: PublicationDocumentsProvider = publication_documents_provider
        self._publication_aoj_repository: PublicationAOJRepository = publication_aoj_repository
        self._template_parser: TemplateParser = template_parser

    def fetch_data(
        self,
        session: Session,
        publication_version: PublicationVersionTable,
        bill_frbr: BillFrbr,
        act_frbr: ActFrbr,
    ) -> PublicationData:
        objects: List[dict] = self._publication_object_provider.get_objects(session, publication_version)
        parsed_template = self._template_parser.get_parsed_template(
            publication_version.Publication.Template.Text_Template,
            objects,
        )
        used_object_codes: Set[str] = self._get_used_object_codes(parsed_template)
        used_objects: List[dict] = self._get_used_objects(objects, used_object_codes)
        assets: List[dict] = self._publication_asset_provider.get_assets(session, used_objects)

        # The gebiedsaanwijzingen service mutates the objects therefor we get the used objects back
        gebiedsaanwijzingen: List[GebiedsaanwijzingData] = []
        used_objects, gebiedsaanwijzingen = self._publication_gebiedsaanwijzingen_provider.get_gebiedsaanwijzingen(
            objects,
            used_objects,
        )
        gebieden_data: GebiedenData = self._publication_gebieden_provider.get_gebieden_data(
            objects,
            used_objects,
        )
        geo_data: PublicationGeoData = self._publication_gios_provider.process(
            session,
            act_frbr,
            gebieden_data,
            gebiedsaanwijzingen,
        )

        documents: List[dict] = self._publication_documents_provider.get_documents(
            session,
            act_frbr,
            objects,
            used_objects,
        )
        area_of_jurisdiction: dict = self._get_aoj(session, publication_version.Created_Date)
        bill_attachments: List[dict] = self._get_bill_attachments(publication_version, bill_frbr)

        result: PublicationData = PublicationData(
            used_object_codes=used_object_codes,
            objects=used_objects,
            documents=documents,
            assets=assets,
            gios=geo_data.gios,
            gebiedengroepen=geo_data.gebiedengroepen,
            gebiedsaanwijzingen=geo_data.gebiedsaanwijzingen,
            bill_attachments=bill_attachments,
            area_of_jurisdiction=area_of_jurisdiction,
            parsed_template=parsed_template,
        )
        return result

    def _get_used_object_codes(self, text_template: str) -> Set[str]:
        soup = BeautifulSoup(text_template, "html.parser")
        objects = soup.find_all("object")
        codes: List[str] = [obj.get("code") for obj in objects if obj.get("code")]
        result: Set[str] = set(codes)
        return result

    def _get_used_objects(self, objects: List[dict], used_object_codes: Set[str]) -> List[dict]:
        results: List[dict] = [o for o in objects if o["Code"] in used_object_codes]
        return results

    def _get_aoj(self, session: Session, before_datetime: Optional[datetime] = None) -> dict:
        aoj: Optional[PublicationAreaOfJurisdictionTable] = self._publication_aoj_repository.get_latest(
            session,
            before_datetime,
        )
        if aoj is None:
            raise validation_exception(
                [
                    ValidatePublicationError(
                        rule="ambtsgebied_does_not_exist",
                        messages=["There needs to be an area of jurisdiction"],
                    )
                ]
            )

        result: dict = {
            "UUID": aoj.UUID,
            "Title": aoj.Title,
            "Administrative_Borders_ID": aoj.Administrative_Borders_ID,
            "Administrative_Borders_Domain": aoj.Administrative_Borders_Domain,
            "Administrative_Borders_Date": aoj.Administrative_Borders_Date,
            "Created_Date": aoj.Created_Date,
        }
        return result

    def _get_bill_attachments(self, publication_version: PublicationVersionTable, bill_frbr: BillFrbr) -> List[dict]:
        result: List[dict] = []

        for attachment in publication_version.Attachments:
            work_other = f"pdf-{bill_frbr.Work_Other}-{attachment.ID}"

            frbr = dso_models.PubdataFRBR(
                Work_Province_ID=bill_frbr.Work_Province_ID,
                Work_Date=bill_frbr.Work_Date,
                Work_Other=work_other,
                Expression_Language=bill_frbr.Expression_Language,
                Expression_Date=bill_frbr.Expression_Date,
                Expression_Version=1,
            )
            attachment_dict: dict = {
                "id": attachment.ID,
                "uuid": attachment.File.UUID,
                "filename": attachment.Filename,
                "title": attachment.Title,
                "binary": attachment.File.Binary,
                "frbr": frbr,
            }
            result.append(attachment_dict)

        return result

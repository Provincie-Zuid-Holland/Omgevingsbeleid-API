from typing import List, Optional, Set

import dso.models as dso_models
from bs4 import BeautifulSoup

from app.extensions.publications.models.api_input_data import ActFrbr, BillFrbr, PublicationData
from app.extensions.publications.repository import PublicationObjectRepository
from app.extensions.publications.repository.publication_aoj_repository import PublicationAOJRepository
from app.extensions.publications.services.act_package.werkingsgebieden_provider import (
    PublicationWerkingsgebiedenProvider,
)
from app.extensions.publications.services.assets.publication_asset_provider import PublicationAssetProvider
from app.extensions.publications.services.template_parser import TemplateParser
from app.extensions.publications.tables.tables import PublicationAreaOfJurisdictionTable, PublicationVersionTable


class ActPublicationDataProvider:
    def __init__(
        self,
        publication_object_repository: PublicationObjectRepository,
        publication_asset_provider: PublicationAssetProvider,
        publication_werkingsgebieden_provider: PublicationWerkingsgebiedenProvider,
        publication_aoj_repository: PublicationAOJRepository,
        template_parser: TemplateParser,
    ):
        self._publication_object_repository: PublicationObjectRepository = publication_object_repository
        self._publication_asset_provider: PublicationAssetProvider = publication_asset_provider
        self._publication_werkingsgebieden_provider: PublicationWerkingsgebiedenProvider = (
            publication_werkingsgebieden_provider
        )
        self._publication_aoj_repository: PublicationAOJRepository = publication_aoj_repository
        self._template_parser: TemplateParser = template_parser

    def fetch_data(
        self,
        publication_version: PublicationVersionTable,
        bill_frbr: BillFrbr,
        act_frbr: ActFrbr,
        all_data: bool = False,
    ) -> PublicationData:
        objects: List[dict] = self._get_objects(publication_version)
        parsed_template = self._template_parser.get_parsed_template(
            publication_version.Publication.Template.Text_Template,
            objects,
        )
        used_object_codes: Set[str] = self._get_used_object_codes(parsed_template)
        used_objects: List[dict] = self._get_used_objects(objects, used_object_codes)
        assets: List[dict] = self._publication_asset_provider.get_assets(used_objects)
        werkingsgebieden: List[dict] = self._publication_werkingsgebieden_provider.get_werkingsgebieden(
            act_frbr,
            objects,
            used_objects,
            all_data,
        )
        area_of_jurisdiction: dict = self._get_aoj()
        attachments: List[dict] = self._get_attachments(publication_version, bill_frbr)

        result: PublicationData = PublicationData(
            objects=used_objects,
            assets=assets,
            werkingsgebieden=werkingsgebieden,
            attachments=attachments,
            area_of_jurisdiction=area_of_jurisdiction,
            parsed_template=parsed_template,
        )
        return result

    def _get_objects(self, publication_version: PublicationVersionTable) -> List[dict]:
        objects: List[dict] = self._publication_object_repository.fetch_objects(
            publication_version.Publication.Module_ID,
            publication_version.Module_Status.Created_Date,
            publication_version.Publication.Template.Object_Types,
            publication_version.Publication.Template.Field_Map,
        )
        return objects

    def _get_used_object_codes(self, text_template: str) -> Set[str]:
        soup = BeautifulSoup(text_template, "html.parser")
        objects = soup.find_all("object")
        codes: List[str] = [obj.get("code") for obj in objects]
        result: Set[str] = set(codes)
        return result

    def _get_used_objects(self, objects: List[dict], used_object_codes: Set[str]) -> List[dict]:
        results: List[dict] = [o for o in objects if o["Code"] in used_object_codes]
        return results

    def _get_aoj(self) -> dict:
        aoj: Optional[PublicationAreaOfJurisdictionTable] = self._publication_aoj_repository.get_latest()
        if aoj is None:
            raise RuntimeError("There needs to be an area of jurisdiction")

        result: dict = {
            "UUID": aoj.UUID,
            "Title": aoj.Title,
            "Administrative_Borders_ID": aoj.Administrative_Borders_ID,
            "Administrative_Borders_Domain": aoj.Administrative_Borders_Domain,
            "Administrative_Borders_Date": aoj.Administrative_Borders_Date,
            "Created_Date": aoj.Created_Date,
        }
        return result

    def _get_attachments(self, publication_version: PublicationVersionTable, bill_frbr: BillFrbr) -> List[dict]:
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

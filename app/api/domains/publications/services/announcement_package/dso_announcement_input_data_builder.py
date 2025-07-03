import uuid
from datetime import date, datetime
from typing import List, Optional

import dso.models as dso_models
from dso.announcement_builder.state_manager.models import InputData, Kennisgeving

from app.api.domains.publications.types.api_input_data import ApiAnnouncementInputData, BillFrbr, DocFrbr
from app.api.domains.publications.types.enums import DocumentType, PackageType, ProcedureType
from app.api.domains.publications.types.models import AnnouncementContent, AnnouncementProcedural
from app.api.domains.publications.types.waardelijsten import Onderwerp
from app.core.tables.publications import PublicationAnnouncementTable, PublicationEnvironmentTable

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


class DsoAnnouncementInputDataBuilder:
    def __init__(self, api_input_data: ApiAnnouncementInputData):
        self._api_input_data: ApiAnnouncementInputData = api_input_data
        self._environment: PublicationEnvironmentTable = api_input_data.Announcement.Publication.Environment
        self._announcement: PublicationAnnouncementTable = api_input_data.Announcement
        self._doc_frbr: DocFrbr = api_input_data.Doc_Frbr
        self._about_bill_frbr: BillFrbr = api_input_data.About_Bill_Frbr
        self._procedural: AnnouncementProcedural = api_input_data.Announcement_Procedural
        self._announcement_content: AnnouncementContent = api_input_data.Announcement_Content

    def build(self) -> InputData:
        input_data: InputData = InputData(
            provincie_id=self._environment.Province_ID,
            provincie_ref=f"/tooi/id/provincie/{self._environment.Province_ID}",
            opdracht=self._get_opdracht(),
            bekendmaking_frbr=self._get_doc_frbr(),
            kennisgeving=self._get_kennisgeving(),
            procedure_verloop=self._get_procedure_verloop(),
            kennisgeving_tekst=self._get_kennisgeving_tekst(),
        )
        return input_data

    def _get_opdracht(self) -> dso_models.PublicatieOpdracht:
        dso_opdracht_type: str = OPDRACHT_TYPE_MAP[self._api_input_data.Package_Type]
        result = dso_models.PublicatieOpdracht(
            opdracht_type=dso_opdracht_type,
            id_levering=str(uuid.uuid4()),
            id_bevoegdgezag=self._environment.Authority_ID,
            id_aanleveraar=self._environment.Submitter_ID,
            publicatie_bestand=self._get_akn_filename(),
            datum_bekendmaking=self._announcement.Announcement_Date.strftime("%Y-%m-%d"),
        )
        return result

    def _get_doc_frbr(self) -> dso_models.DocFRBR:
        result = dso_models.DocFRBR(
            Work_Province_ID=self._environment.Province_ID,
            Work_Country=self._doc_frbr.Work_Country,
            Work_Date=self._doc_frbr.Work_Date,
            Work_Other=self._doc_frbr.Work_Other,
            Expression_Language=self._doc_frbr.Expression_Language,
            Expression_Date=self._doc_frbr.Expression_Date,
            Expression_Version=self._doc_frbr.Expression_Version,
        )
        return result

    def _get_about_bill_frbr(self) -> dso_models.BillFRBR:
        result = dso_models.BillFRBR(
            Work_Province_ID=self._environment.Province_ID,
            Work_Country=self._about_bill_frbr.Work_Country,
            Work_Date=self._about_bill_frbr.Work_Date,
            Work_Other=self._about_bill_frbr.Work_Other,
            Expression_Language=self._about_bill_frbr.Expression_Language,
            Expression_Date=self._about_bill_frbr.Expression_Date,
            Expression_Version=self._about_bill_frbr.Expression_Version,
        )
        return result

    def _get_kennisgeving(self) -> Kennisgeving:
        result = Kennisgeving(
            officiele_titel=self._api_input_data.Announcement_Metadata.Official_Title,
            onderwerpen=self._get_onderwerpen(),
            mededeling_over_frbr=self._get_about_bill_frbr(),
        )

        return result

    def _get_onderwerpen(self) -> List[str]:
        result: List[str] = [Onderwerp[v] for v in self._api_input_data.Announcement_Metadata.Subjects]
        return result

    def _get_procedure_verloop(self) -> dso_models.ProcedureVerloop:
        steps: List[dso_models.ProcedureStap] = []

        field_map: List[dict] = [
            {
                "field": "Begin_Inspection_Period_Date",
                "target": dso_models.ProcedureStappen.Begin_inzagetermijn,
                "required": True,
            },
            {
                "field": "End_Inspection_Period_Date",
                "target": dso_models.ProcedureStappen.Einde_inzagetermijn,
                "required": True,
            },
        ]

        for setting in field_map:
            date_value: Optional[str] = getattr(self._procedural, setting["field"])
            if date_value is None and setting["required"]:
                raise RuntimeError(f"Procedural.{setting['field']} is required")

            if date_value is not None:
                steps.append(
                    dso_models.ProcedureStap(
                        soort_stap=setting["target"],
                        voltooid_op=date_value,
                    )
                )

        procedure_verloop = dso_models.ProcedureVerloop(
            bekend_op=self._procedural.Procedural_Announcement_Date,
            stappen=steps,
        )
        return procedure_verloop

    def _get_akn_filename(self) -> str:
        package_type: str = (self._api_input_data.Package_Type[:3]).lower()
        filename: str = (
            f"akn_nl_doc_{self._environment.Province_ID}-{package_type}-{self._doc_frbr.Work_Date}-{self._doc_frbr.Work_Other}-{self._doc_frbr.Expression_Version}.xml"
        )
        return filename

    def _get_kennisgeving_tekst(self) -> str:
        if len(self._announcement_content.Texts) == 0:
            raise RuntimeError("Expecting at least one text (article)")

        pieces: List[str] = []
        for data in self._announcement_content.Texts:
            description: str = data.Description
            description = self._replace_placeholders(description)

            # @todo: parse dates and other placeholders
            html = f"""<div data-hint-element="divisietekst"><h1>{data.Title}</h1>{description}</div>"""
            pieces.append(html)
        result: str = "\n".join(pieces)

        return result

    def _get_readable_date(self, d: date) -> str:
        formatted_date = f"{d.day} {DUTCH_MONTHS[d.month]} {d.year}"
        return formatted_date

    def _get_readable_date_from_str(self, date_str: str) -> str:
        d: date = datetime.strptime(date_str, "%Y-%m-%d")
        result: str = self._get_readable_date(d)
        return result

    def _get_readable_date_short(self, d: date) -> str:
        formatted_date = f"{d.day} {DUTCH_MONTHS[d.month]}"
        return formatted_date

    def _get_readable_date_from_str_short(self, date_str: str) -> str:
        d: date = datetime.strptime(date_str, "%Y-%m-%d")
        result: str = self._get_readable_date_short(d)
        return result

    def _replace_placeholders(self, content: str) -> str:
        content = content.replace(
            "[[BILL_URL]]",
            f"""<a href="{self._about_bill_frbr.get_work()}/{self._about_bill_frbr.get_expression_version()}">www.officielebekendmakingen.nl</a>""",
        )

        begin_date: Optional[str] = self._procedural.Begin_Inspection_Period_Date
        if begin_date is not None:
            date_readable: str = self._get_readable_date_from_str(begin_date)
            content = content.replace("[[BEGIN_INSPECTION_DATE]]", date_readable)
            date_readable: str = self._get_readable_date_from_str_short(begin_date)
            content = content.replace("[[BEGIN_INSPECTION_DATE_SHORT]]", date_readable)

        end_date: Optional[str] = self._procedural.End_Inspection_Period_Date
        if end_date is not None:
            date_readable: str = self._get_readable_date_from_str(end_date)
            content = content.replace("[[END_INSPECTION_DATE]]", date_readable)
            date_readable: str = self._get_readable_date_from_str_short(end_date)
            content = content.replace("[[END_INSPECTION_DATE_SHORT]]", date_readable)

        return content

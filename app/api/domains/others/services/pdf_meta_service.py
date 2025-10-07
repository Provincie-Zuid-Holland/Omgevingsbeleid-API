import io
from enum import Enum
from typing import List

import pikepdf
from pikepdf import Dictionary, Object, PdfImage, Pdf
from pydantic import BaseModel


class PdfMetaReportType(str, Enum):
    PDF_DOCUMENT = "PDF document"
    PDF_IMAGE = "Image in PDF document"


class PdfMetaReport(BaseModel):
    key: str
    value: str
    type: str


BAN_LIST = ["author", "creator"]


class PdfMetaService:
    def report_banned_meta(self, pdf_bytes: bytes) -> List[PdfMetaReport]:
        pdf = pikepdf.open(io.BytesIO(pdf_bytes))
        report_list: List[PdfMetaReport] = []
        report_list += self._check_doc_info(pdf.docinfo)
        report_list += self._check_doc_meta_data(pdf.Root)
        report_list += self._check_pdf_image_meta_data(pdf)
        return report_list

    def _check_doc_info(self, doc_info: Dictionary) -> List[PdfMetaReport]:
        report_list: List[PdfMetaReport] = []

        for meta_key, meta_value in doc_info.items():
            meta_key_clean = self._clean_key(meta_key)
            for ban_key in BAN_LIST:
                if ban_key == meta_key_clean and len(str(meta_value)) > 0:
                    report_list.append(
                        PdfMetaReport(key=meta_key, value=str(meta_value), type=PdfMetaReportType.PDF_DOCUMENT)
                    )
        return report_list

    def _check_doc_meta_data(self, pdf_root_node: Object) -> List[PdfMetaReport]:
        if "/Metadata" not in pdf_root_node:
            return []

        report_list: List[PdfMetaReport] = []

        for meta_key in pdf_root_node["/Metadata"]:
            meta_key = str(meta_key)
            meta_key_clean = self._clean_key(meta_key)
            meta_value = str(pdf_root_node["/Metadata"][meta_key])
            for ban_key in BAN_LIST:
                if ban_key == meta_key_clean and len(meta_value) > 0:
                    report_list.append(
                        PdfMetaReport(key=meta_key, value=str(meta_value), type=PdfMetaReportType.PDF_DOCUMENT)
                    )
        return report_list

    def _check_pdf_image_meta_data(self, pdf: Pdf) -> List[PdfMetaReport]:
        report_list: List[PdfMetaReport] = []

        for page in pdf.pages:
            for pdf_image_key in page.images.keys():
                pdf_image = PdfImage(page.images[pdf_image_key])
                image = pdf_image.as_pil_image()
                exif_data = image.getexif()

                for meta_key, meta_value in exif_data.items():
                    meta_key_clean = self._clean_key(meta_key)
                    for ban_key in BAN_LIST:
                        if ban_key == meta_key_clean and len(meta_value) > 0:
                            report_list.append(
                                PdfMetaReport(key=meta_key, value=str(meta_value), type=PdfMetaReportType.PDF_IMAGE)
                            )

                for meta_key, meta_value in image.info.items():
                    meta_key_clean = self._clean_key(meta_key)
                    for ban_key in BAN_LIST:
                        if ban_key == meta_key_clean and len(meta_value) > 0:
                            report_list.append(
                                PdfMetaReport(key=meta_key, value=str(meta_value), type=PdfMetaReportType.PDF_IMAGE)
                            )
        return report_list

    @staticmethod
    def _clean_key(key: str) -> str:
        key = key.lower()
        key = key.lstrip("/")
        return key

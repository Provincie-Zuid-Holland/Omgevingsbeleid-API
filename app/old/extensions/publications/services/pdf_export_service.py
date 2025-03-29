import time
from abc import ABCMeta
from typing import Optional
from urllib.parse import urljoin

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

from app.core_old.settings.dynamic_settings import DynamicSettings
from app.extensions.publications.models.zip import ZipData
from app.extensions.publications.settings import KoopSettings


class PdfExportError(Exception, metaclass=ABCMeta):
    def __init__(self, msg: str):
        self.msg = msg


class PdfExportUnauthorizedError(PdfExportError):
    pass


class PdfExportNotFoundError(PdfExportError):
    pass


class PdfExportXmlError(PdfExportError):
    pass


class PdfExportInternalServerError(PdfExportError):
    pass


class PdfExportTooManyAttemptsError(PdfExportError):
    pass


class PdfExportUnkownError(PdfExportError):
    def __init__(self, msg: str, status_code: int):
        self.msg = msg
        self.status_code = status_code


class PdfExportService:
    def __init__(self, settings: DynamicSettings):
        self._settings: DynamicSettings = settings

    def create_pdf(self, environment_code: str, zip_data: ZipData) -> requests.Response:
        api_settings: KoopSettings = self._get_api_settings(environment_code)
        idx: str = self._request_generate(api_settings, zip_data)
        self._wait_for_completion(api_settings, idx)
        result: requests.Response = self._download_pdf(api_settings, idx)

        return result

    def _request_generate(self, api_settings: KoopSettings, zip_data: ZipData) -> str:
        multipart_data = MultipartEncoder(
            fields={
                "aanlevering-zip": (zip_data.Filename, zip_data.Binary, "application/zip"),
                "voor-ondertekenen": "true",
                "auto-clean-up": "true",
            }
        )
        headers = {
            "x-api-key": api_settings.API_KEY,
            "Content-Type": multipart_data.content_type,
        }
        response = requests.post(
            urljoin(api_settings.PREVIEW_API_URL, "/maak-bekendmaking"),
            headers=headers,
            data=multipart_data,
        )

        match response.status_code:
            case 200 | 202:
                response_body = response.json()
                idx: str = response_body.get("id")
                return idx
            case 403:
                raise PdfExportUnauthorizedError("Pdf export unauthorized")
            case 404:
                raise PdfExportNotFoundError("Pdf export not found")
            case 422:
                raise PdfExportXmlError("Pdf export xml")
            case 500:
                raise PdfExportInternalServerError("Pdf export internal server error")
            case _ as code:
                raise PdfExportUnkownError("Pdf export unkown", code)

    def _wait_for_completion(self, api_settings: KoopSettings, idx: str):
        headers = {
            "x-api-key": api_settings.API_KEY,
        }
        delay_ms: int = 200
        attempts: int = 0

        while True:
            response = requests.get(
                urljoin(api_settings.PREVIEW_API_URL, f"/status/{idx}"),
                headers=headers,
            )

            match response.status_code:
                case 200 | 202:
                    response_body = response.json()
                    status_pdf: str = response_body.get("status-pdf")
                    if status_pdf == "gereed":
                        return
                case 403:
                    raise PdfExportUnauthorizedError(response.text)
                case 404:
                    raise PdfExportNotFoundError(response.text)
                case 422:
                    raise PdfExportXmlError(response.text)
                case 500:
                    raise PdfExportInternalServerError(response.text)
                case _ as code:
                    raise PdfExportUnkownError(response.text, code)

            time.sleep(delay_ms / 1000)
            delay_ms = min(delay_ms * 1.5, 5000)
            attempts += 1
            if attempts >= 20:
                raise PdfExportTooManyAttemptsError("Too many attempts on getting the status")

    def _download_pdf(self, api_settings: KoopSettings, idx: str) -> requests.Response:
        headers = {
            "x-api-key": api_settings.API_KEY,
        }

        response = requests.get(
            urljoin(api_settings.PREVIEW_API_URL, f"/download/{idx}"),
            headers=headers,
            stream=True,
        )

        match response.status_code:
            case 200 | 202:
                return response
            case 403:
                raise PdfExportUnauthorizedError(response.text)
            case 404:
                raise PdfExportNotFoundError(response.text)
            case 422:
                raise PdfExportXmlError(response.text)
            case 500:
                raise PdfExportInternalServerError(response.text)
            case _ as code:
                raise PdfExportUnkownError(response.text, code)

    def _get_api_settings(self, environment_code: str) -> KoopSettings:
        api_settings: Optional[KoopSettings] = self._settings.PUBLICATION_KOOP.get(environment_code)
        if api_settings is None:
            raise RuntimeError("Missing runtime environment settings for this Publication Environment Code")

        return api_settings

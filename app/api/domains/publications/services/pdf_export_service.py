from abc import ABCMeta
from urllib.parse import urljoin

import anyio
import httpx2

from app.api.domains.publications.types.zip import ZipData
from app.core.settings import KoopSettings


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


class PdfExportUnavailableError(PdfExportError):
    pass


class PdfExportUnkownError(PdfExportError):
    def __init__(self, msg: str, status_code: int):
        self.msg = msg
        self.status_code = status_code


class PdfExportService:
    def __init__(self, koop_settings: dict[str, KoopSettings], timeout_seconds: float):
        # @todo: should be parsed by the Settings
        self._koop_settings: dict[str, KoopSettings] = {
            k: KoopSettings(**v) if not isinstance(v, KoopSettings) else v for k, v in koop_settings.items()
        }
        self._timeout_seconds: float = timeout_seconds

    async def healthcheck(self, environment_code: str) -> None:
        try:
            api_settings: KoopSettings = self._get_api_settings(environment_code)

            async with httpx2.AsyncClient(timeout=5) as client:
                response = await client.get(
                    urljoin(api_settings.PREVIEW_API_URL, "/health"),
                    headers={"x-api-key": api_settings.API_KEY},
                )
            if response.status_code >= 500:
                raise PdfExportUnavailableError(f"PDF preview service is unavailable (status {response.status_code})")
        except httpx2.ConnectError:
            raise PdfExportUnavailableError("PDF preview service is unreachable")
        except httpx2.TimeoutException:
            raise PdfExportUnavailableError("PDF preview service timed out")

    async def create_pdf(self, environment_code: str, zip_data: ZipData) -> bytes:
        api_settings: KoopSettings = self._get_api_settings(environment_code)
        async with httpx2.AsyncClient(timeout=self._timeout_seconds) as client:
            idx: str = await self._request_generate(client, api_settings, zip_data)
            await self._wait_for_completion(client, api_settings, idx)
            result: bytes = await self._download_pdf(client, api_settings, idx)

        return result

    async def _request_generate(self, client: httpx2.AsyncClient, api_settings: KoopSettings, zip_data: ZipData) -> str:
        response = await client.post(
            urljoin(api_settings.PREVIEW_API_URL, "/maak-bekendmaking"),
            headers={"x-api-key": api_settings.API_KEY},
            files={"aanlevering-zip": (zip_data.filename, zip_data.binary, "application/zip")},
            data={
                "voor-ondertekenen": "true",
                "auto-clean-up": "true",
            },
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

    async def _wait_for_completion(self, client: httpx2.AsyncClient, api_settings: KoopSettings, idx: str):
        headers = {
            "x-api-key": api_settings.API_KEY,
        }
        delay_ms: int = 200
        attempts: int = 0

        while True:
            response = await client.get(
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

            await anyio.sleep(delay_ms / 1000)
            delay_ms = min(int(delay_ms * 1.5), 5000)
            attempts += 1
            if attempts >= 20:
                raise PdfExportTooManyAttemptsError("Too many attempts on getting the status")

    async def _download_pdf(self, client: httpx2.AsyncClient, api_settings: KoopSettings, idx: str) -> bytes:
        response = await client.get(
            urljoin(api_settings.PREVIEW_API_URL, f"/download/{idx}"),
            headers={"x-api-key": api_settings.API_KEY},
        )

        match response.status_code:
            case 200 | 202:
                return response.content
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
        api_settings: KoopSettings | None = self._koop_settings.get(environment_code)
        if api_settings is None:
            raise RuntimeError("Missing runtime environment settings for this Publication Environment code")

        return api_settings

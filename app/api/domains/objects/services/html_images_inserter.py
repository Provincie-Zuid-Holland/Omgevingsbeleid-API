import re
from typing import List, Optional, Set
from uuid import UUID

from bs4 import BeautifulSoup
from pydantic import BaseModel

from app.api.domains.objects.repositories.asset_repository import AssetRepository
from app.core.tables.others import AssetsTable


class InsertHtmlImagesConfig(BaseModel):
    fields: Set[str]


class HtmlImagesInserter:
    def __init__(
        self,
        asset_repository: AssetRepository,
        rows: List[BaseModel],
        config: InsertHtmlImagesConfig,
    ):
        self._config: InsertHtmlImagesConfig = config
        self._rows: List[BaseModel] = rows
        self._asset_repository: AssetRepository = asset_repository

    def process(self) -> List[BaseModel]:
        for index, row in enumerate(self._rows):
            for field_name in self._config.fields:
                if not hasattr(row, field_name):
                    continue

                content: str = getattr(row, field_name)
                if not isinstance(content, str):
                    continue

                soup = BeautifulSoup(content, "html.parser")

                for img in soup.find_all("img", src=re.compile(r"^\[ASSET")):
                    try:
                        asset_uuid = UUID(img["src"].split(":")[1][:-1])
                    except ValueError:
                        continue

                    asset: Optional[AssetsTable] = self._asset_repository.get_by_uuid(asset_uuid)
                    if not asset:
                        continue

                    img["src"] = asset.Content

                setattr(row, field_name, str(soup))

        return self._rows


class HtmlImagesInserterFactory:
    def __init__(self, asset_repository: AssetRepository):
        self._asset_repository: AssetRepository = asset_repository

    def create_service(
        self,
        rows: List[BaseModel],
        config: InsertHtmlImagesConfig,
    ) -> HtmlImagesInserter:
        return HtmlImagesInserter(
            asset_repository=self._asset_repository,
            rows=rows,
            config=config,
        )

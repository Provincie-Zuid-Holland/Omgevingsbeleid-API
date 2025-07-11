from typing import List, Optional, Set
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.objects.repositories.asset_repository import AssetRepository
from app.core.tables.others import AssetsTable


class GetImagesConfig(BaseModel):
    fields: Set[str]


class ColumnImageInserter:
    def __init__(
        self,
        session: Session,
        asset_repository: AssetRepository,
        rows: List[BaseModel],
        config: GetImagesConfig,
    ):
        self._session: Session = session
        self._config: GetImagesConfig = config
        self._rows: List[BaseModel] = rows
        self._asset_repository: AssetRepository = asset_repository

    def process(self) -> List[BaseModel]:
        for index, row in enumerate(self._rows):
            for field_name in self._config.fields:
                if not hasattr(row, field_name):
                    continue

                content: str = getattr(row, field_name)
                if not content:
                    continue

                try:
                    image_uuid = UUID(content)
                except ValueError:
                    continue

                asset: Optional[AssetsTable] = self._asset_repository.get_by_uuid(self._session, image_uuid)
                if not asset:
                    continue

                setattr(row, field_name, asset.Content)

        return self._rows


class ColumnImageInserterFactory:
    def __init__(self, asset_repository: AssetRepository):
        self._asset_repository: AssetRepository = asset_repository

    def create_service(
        self,
        session: Session,
        rows: List[BaseModel],
        config: GetImagesConfig,
    ) -> ColumnImageInserter:
        return ColumnImageInserter(
            session=session,
            asset_repository=self._asset_repository,
            rows=rows,
            config=config,
        )

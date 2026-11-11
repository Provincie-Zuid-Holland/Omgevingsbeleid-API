from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.domains.objects.repositories.asset_repository import AssetRepository
from app.core.tables.others import AssetsTable


class GetImagesConfig(BaseModel):
    fields: set[str]


class ColumnImageInserter:
    def __init__(
        self,
        session: AsyncSession,
        asset_repository: AssetRepository,
        rows: list[BaseModel],
        config: GetImagesConfig,
    ):
        self._session: AsyncSession = session
        self._config: GetImagesConfig = config
        self._rows: list[BaseModel] = rows
        self._asset_repository: AssetRepository = asset_repository

    async def process(self) -> list[BaseModel]:
        for index, row in enumerate(self._rows):
            for field_name in self._config.fields:
                if not hasattr(row, field_name):
                    continue

                content: str = getattr(row, field_name)
                if not content:
                    continue

                try:
                    image_id = UUID(content)
                except ValueError:
                    continue

                asset: AssetsTable | None = await self._asset_repository.get_by_id(self._session, image_id)
                if not asset:
                    continue

                setattr(row, field_name, asset.content)

        return self._rows


class ColumnImageInserterFactory:
    def __init__(self, asset_repository: AssetRepository):
        self._asset_repository: AssetRepository = asset_repository

    def create_service(
        self,
        session: AsyncSession,
        rows: list[BaseModel],
        config: GetImagesConfig,
    ) -> ColumnImageInserter:
        return ColumnImageInserter(
            session=session,
            asset_repository=self._asset_repository,
            rows=rows,
            config=config,
        )

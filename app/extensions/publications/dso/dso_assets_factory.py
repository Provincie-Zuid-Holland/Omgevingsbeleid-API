import json
import re
from typing import List, Set
from uuid import UUID

from bs4 import BeautifulSoup
from dso.builder.state_manager.input_data.resource.asset.asset_repository import AssetRepository as DSOAssetRepository

from app.extensions.html_assets.db.tables import AssetsTable
from app.extensions.html_assets.repository.assets_repository import AssetRepository

asset_re = re.compile("^\[ASSET")


class DsoAssetsFactory:
    def __init__(self, asset_repository: AssetRepository):
        self._asset_repository: AssetRepository = asset_repository

    def get_repository_for_objects(self, objects: List[dict]) -> DSOAssetRepository:
        asset_uuids = self._calculate_asset_uuids(objects)
        assets: List[AssetsTable] = self._asset_repository.get_by_uuids(asset_uuids)
        repository: DSOAssetRepository = self._get_asset_repository(assets)

        return repository

    def _calculate_asset_uuids(self, objects: List[dict]) -> List[UUID]:
        asset_uuids: Set[UUID] = set()

        asset_fields = [
            "Description",
            "Cause",
            "Provincial_Interest",
            "Explanation",
        ]

        for o in objects:
            for field in asset_fields:
                value = o.get(field, None)
                if value is None:
                    continue

                soup = BeautifulSoup(value, "html.parser")
                for img in soup.find_all("img", src=asset_re):
                    try:
                        asset_uuid = UUID(img["src"].split(":")[1][:-1])
                        asset_uuids.add(asset_uuid)
                    except ValueError:
                        continue

        return list(asset_uuids)

    def _get_asset_repository(self, assets: List[AssetsTable]) -> DSOAssetRepository:
        repository = DSOAssetRepository()

        for asset in assets:
            asset_dict = {
                "UUID": str(asset.UUID),
                "Created_Date": str(asset.Created_Date),
                "Meta": json.loads(asset.Meta),
                "Content": asset.Content,
            }
            repository.add(asset_dict)

        return repository

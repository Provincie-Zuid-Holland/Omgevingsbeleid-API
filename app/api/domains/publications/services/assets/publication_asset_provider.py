import json
import re
import uuid
from typing import List, Sequence, Set

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.api.domains.objects.repositories.asset_repository import AssetRepository
from app.api.domains.publications.services.assets.asset_remove_transparency import AssetRemoveTransparency
from app.core.tables.others import AssetsTable

asset_re = re.compile(r"^\[ASSET")


class PublicationAssetProvider:
    def __init__(
        self,
        asset_repository: AssetRepository,
        asset_remove_transparency: AssetRemoveTransparency,
    ):
        self._asset_repository: AssetRepository = asset_repository
        self._asset_remove_transparency: AssetRemoveTransparency = asset_remove_transparency

    def get_assets(self, session: Session, objects: List[dict]) -> List[dict]:
        asset_uuids: List[uuid.UUID] = self._calculate_asset_uuids(objects)
        dso_assets: List[dict] = self.get_assets_by_uuids(session, asset_uuids)

        return dso_assets

    def get_assets_by_uuids(self, session: Session, uuids: List[uuid.UUID]) -> List[dict]:
        assets: Sequence[AssetsTable] = self._asset_repository.get_by_uuids(session, uuids)
        dso_assets: List[dict] = self._as_dso_assets(assets)

        return dso_assets

    def _calculate_asset_uuids(self, objects: List[dict]) -> List[uuid.UUID]:
        asset_uuids: Set[uuid.UUID] = set()

        # @todo: should be provided somewhere
        asset_fields = [
            "Description",
            "Cause",
            "Provincial_Interest",
            "Explanation",
            "Effect",
        ]

        for o in objects:
            for field in asset_fields:
                value = o.get(field, None)
                if value is None:
                    continue

                soup = BeautifulSoup(value, "html.parser")
                for img in soup.find_all("img", src=asset_re):
                    try:
                        asset_uuid = uuid.UUID(img["src"].split(":")[1][:-1])
                        asset_uuids.add(asset_uuid)
                    except ValueError:
                        continue

        return list(asset_uuids)

    def _as_dso_assets(self, assets: Sequence[AssetsTable]) -> List[dict]:
        dso_assets: List[dict] = []

        for asset in assets:
            content = asset.Content
            meta = json.loads(asset.Meta)
            content, meta = self._asset_remove_transparency.fix(content, meta)

            asset_dict = {
                "UUID": str(asset.UUID),
                "Created_Date": str(asset.Created_Date),
                "Meta": meta,
                "Content": content,
            }
            dso_assets.append(asset_dict)

        return dso_assets

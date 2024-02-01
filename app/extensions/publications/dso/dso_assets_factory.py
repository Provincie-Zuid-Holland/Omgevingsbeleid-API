import base64
import json
import re
from io import BytesIO
from typing import List, Set, Tuple
from uuid import UUID

from bs4 import BeautifulSoup
from dso.builder.state_manager.input_data.resource.asset.asset_repository import AssetRepository as DSOAssetRepository
from PIL import Image

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
            content = asset.Content
            meta = json.loads(asset.Meta)
            content, meta = self._make_dso_compatible(content, meta)

            asset_dict = {
                "UUID": str(asset.UUID),
                "Created_Date": str(asset.Created_Date),
                "Meta": meta,
                "Content": content,
            }
            repository.add(asset_dict)

        return repository

    def _make_dso_compatible(self, content: str, meta: dict) -> Tuple[str, dict]:
        if meta["ext"] == "png":
            content, meta = self._fix_transparancy(content, meta)

        return content, meta

    def _fix_transparancy(self, content: str, meta: dict) -> Tuple[str, dict]:
        try:
            base64_format_match = re.match(r"data:image/(.*?);base64,(.*)", content)
            mime_type, base64_data = base64_format_match.groups()

            original_image_data = base64.b64decode(base64_data)
            original_image = Image.open(BytesIO(original_image_data))

            has_transparency = original_image.mode == "RGBA" or "transparency" in original_image.info
            if not has_transparency:
                return content, meta

            rgb_image = Image.new("RGB", original_image.size, (255, 255, 255))
            if original_image.mode == "RGBA":
                mask = original_image.split()[3]
                rgb_image.paste(original_image, (0, 0), mask=mask)
            else:
                rgb_image.paste(original_image, (0, 0))

            # rgb_image = rgb_image.convert("RGB")

            # Convert back to base64
            rgb_image_arr = BytesIO()
            rgb_image.save(rgb_image_arr, format="PNG")
            rgb_image_arr = rgb_image_arr.getvalue()

            new_content = base64.b64encode(rgb_image_arr).decode()
            new_content = f"data:image/{mime_type};base64,{new_content}"

            meta["size"] = len(rgb_image_arr)

            return new_content, meta
        except Exception as e:
            a = True

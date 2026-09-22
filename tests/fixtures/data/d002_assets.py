from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.asset_spec import AssetSpec


def load(col: Collector) -> None:
    col.adds(
        [
            AssetSpec(
                key="blue",
                file_path="./rectangle-blue.png",
            ),
            AssetSpec(
                key="green",
                file_path="./rectangle-green.png",
            ),
            AssetSpec(
                key="yellow",
                file_path="./rectangle-yellow.png",
            ),
        ]
    )

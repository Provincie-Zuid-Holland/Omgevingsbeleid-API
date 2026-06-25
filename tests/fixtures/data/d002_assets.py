from tests.fixtures.internal.services.collector import Collector
from tests.fixtures.internal.spec.asset_spec import AssetSpec


def load(col: Collector) -> None:
    col.adds(
        [
            AssetSpec(
                key="blue",
                File_Path="./rectangle-blue.png",
            ),
            AssetSpec(
                key="green",
                File_Path="./rectangle-green.png",
            ),
            AssetSpec(
                key="yellow",
                File_Path="./rectangle-yellow.png",
            ),
        ]
    )

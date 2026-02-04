from typing import Annotated

from fastapi import Depends

from app.api.domains.werkingsgebieden.dependencies import depends_input_geo_werkingsgebied
from app.api.domains.werkingsgebieden.types import InputGeoWerkingsgebiedDetailed
from app.core.tables.werkingsgebieden import InputGeoWerkingsgebiedenTable


def get_input_geo_werkingsgebieden_detail_endpoint(
    input_geo_werkingsgebied: Annotated[InputGeoWerkingsgebiedenTable, Depends(depends_input_geo_werkingsgebied)],
) -> InputGeoWerkingsgebiedDetailed:
    result: InputGeoWerkingsgebiedDetailed = InputGeoWerkingsgebiedDetailed.model_validate(input_geo_werkingsgebied)
    return result

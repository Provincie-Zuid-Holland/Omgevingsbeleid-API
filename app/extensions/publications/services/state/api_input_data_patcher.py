from app.extensions.publications.models.api_input_data import ApiInputData
from app.extensions.publications.services.state.state import ActiveState


class ApiInputDataPatcher:
    def __init__(self, state: ActiveState):
        self._state: ActiveState = state

    def apply(self, data: ApiInputData) -> ApiInputData:
        data = self._patch_werkingsgebieden(data)
        data = self._patch_area_of_jurisdiction(data)
        return data

    def _patch_werkingsgebieden(self, data: ApiInputData) -> ApiInputData:
        for index, werkingsgebied in enumerate(data.Publication_Data.werkingsgebieden):
            has_this_werkingsgebied: bool = self._state.has_werkingsgebied(werkingsgebied)
            data.Publication_Data.werkingsgebieden[index]["New"] = not has_this_werkingsgebied
        return data

    def _patch_area_of_jurisdiction(self, data: ApiInputData) -> ApiInputData:
        has_this_aoj: bool = self._state.has_area_of_jurisdiction(data.Publication_Data.area_of_jurisdiction)
        data.Publication_Data.area_of_jurisdiction["New"] = not has_this_aoj
        return data

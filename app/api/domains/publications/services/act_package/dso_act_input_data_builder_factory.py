from typing import Dict

from app.api.domains.publications.services.act_package.dso_act_input_data_builder import DsoActInputDataBuilder
from app.api.domains.publications.types.api_input_data import ApiActInputData
from app.core.settings import KoopSettings


class DsoActInputDataBuilderFactory:
    def __init__(self, koop_settings: Dict[str, KoopSettings]):
        self._koop_settings: Dict[str, KoopSettings] = koop_settings

    def create(self, api_input_data: ApiActInputData) -> DsoActInputDataBuilder:
        return DsoActInputDataBuilder(
            self._koop_settings,
            api_input_data,
        )

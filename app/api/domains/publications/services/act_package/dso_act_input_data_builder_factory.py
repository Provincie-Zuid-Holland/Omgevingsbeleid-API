from typing import Dict

from app.api.domains.publications.services.act_package.dso_act_input_data_builder import DsoActInputDataBuilder
from app.api.domains.publications.types.api_input_data import ApiActInputData
from app.core.settings import KoopSettings


class DsoActInputDataBuilderFactory:
    def __init__(self, koop_settings: Dict[str, KoopSettings]):
        # @todo: The Dependency Injector config only support flat dicts
        # So we need to convert the KoopSettings to a dict
        # But we should just update the containers that we have pydantic settings instead of DI config
        self._koop_settings: Dict[str, KoopSettings] = {
            key: KoopSettings.model_validate(settings) for key, settings in koop_settings.items()
        }

    def create(self, api_input_data: ApiActInputData) -> DsoActInputDataBuilder:
        return DsoActInputDataBuilder(
            self._koop_settings,
            api_input_data,
        )

from app.api.domains.publications.types.models import ActMetadata
from app.core.services.main_config import MainConfig


class ActDefaultsProvider:
    def __init__(self, main_config: MainConfig):
        main_config_dict: dict = main_config.get_main_config()
        self._defaults: dict = main_config_dict["publication"]["act_defaults"]

    def get_metadata(self, document_type: str) -> ActMetadata:
        key: str = document_type
        defaults: dict = self._defaults[key]["metadata"]
        result: ActMetadata = ActMetadata(**defaults)
        return result

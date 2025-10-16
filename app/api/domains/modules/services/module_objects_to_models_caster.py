from typing import List, Any, Dict

from app.core.services import ModelsProvider
from app.core.tables.modules import ModuleObjectsTable


class ModuleObjectsToModelsCaster:
    def __init__(self, models_provider: ModelsProvider):
        self._models_provider = models_provider

    def cast(self, module_objects: List[ModuleObjectsTable], model_map: Dict[str, str]) -> Dict[str, Any]:
        result = {}
        for object_current in module_objects:
            model_id = model_map.get(object_current.Object_Type)
            if model_id is None:
                continue
            pydantic_model = self._models_provider.get_pydantic_model(model_id)
            model_instance = pydantic_model.model_validate(object_current)
            result[object_current.Object_ID] = model_instance

        return result

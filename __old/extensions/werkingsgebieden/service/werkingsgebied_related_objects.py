from typing import List

from pydantic import BaseModel

from app.dynamic.computed_fields.models import ComputedField
from app.dynamic.config.models import DynamicObjectModel
from app.dynamic.db.tables import ObjectsTable
from app.extensions.modules.repository.module_object_repository import LatestObjectPerModuleResult
from app.extensions.modules.repository.object_provider import ObjectProvider
from app.extensions.werkingsgebieden.models.models import (
    DynamicModuleObjectShort,
    DynamicObjectShort,
    WerkingsgebiedRelatedObjects,
)


class WerkingsgebiedRelatedObjectService:
    def __init__(
        self,
        object_provider: ObjectProvider,
        rows: List[BaseModel],
        dynamic_obj_model: DynamicObjectModel,
        computed_field: ComputedField,
    ):
        self._object_provider = object_provider
        self._rows: List[BaseModel] = rows
        self._dynamic_obj_model: DynamicObjectModel = dynamic_obj_model
        self._computed_field: ComputedField = computed_field

    def fetch_related_objects(self) -> BaseModel:
        if len(self._rows) != 1:
            raise ValueError("Trying to process a single obj but multiple rows found")

        item = self._rows[0]
        related_rows: List[LatestObjectPerModuleResult | ObjectsTable] = (
            self._object_provider.list_all_objects_related_to_werkingsgebied(werkingsgebied_code=getattr(item, "Code"))
        )
        field_name: str = self._computed_field.attribute_name
        result: WerkingsgebiedRelatedObjects = self._process_related_objects(related_rows)
        setattr(item, field_name, result)

        return item

    def _process_related_objects(self, related_rows) -> WerkingsgebiedRelatedObjects:
        related_objects = []
        related_module_objects = []

        for row in related_rows:
            match row:
                case ObjectsTable():
                    related_objects.append(
                        DynamicObjectShort(
                            UUID=row.UUID, Object_ID=row.Object_ID, Object_Type=row.Object_Type, Title=row.Title
                        )
                    )
                case LatestObjectPerModuleResult():
                    related_module_objects.append(
                        DynamicModuleObjectShort(
                            UUID=row.module_object.UUID,
                            Object_ID=row.module_object.Object_ID,
                            Object_Type=row.module_object.Object_Type,
                            Title=row.module_object.Title,
                            Module_ID=row.module.Module_ID,
                            Module_Title=row.module.Title,
                        )
                    )

        return WerkingsgebiedRelatedObjects(Valid_Objects=related_objects, Module_Objects=related_module_objects)

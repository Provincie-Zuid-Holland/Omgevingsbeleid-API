from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dynamic.db.tables import ObjectsTable
from app.dynamic.event.retrieved_objects_event import RetrievedObjectsEvent
from app.dynamic.event.types import Listener
from app.dynamic.repository.object_repository import ObjectRepository
from app.extensions.modules.models.models import DynamicModuleObjectShort, DynamicObjectShort, WerkingsgebiedRelatedObjects
from app.extensions.modules.repository.module_object_repository import LatestObjectPerModuleResult, ModuleObjectRepository
from app.extensions.modules.repository.object_provider import ObjectProvider


class WerkingsgebiedRelatedObjectService:
    def __init__(
        self,
        event: RetrievedObjectsEvent,
        target_field: str,
    ):
        self._target_field: str = target_field
        self._event_objects: List[BaseModel] = event.payload.rows
        self._db: Session = event.get_db()
        self._object_provider = ObjectProvider(
            object_repository=ObjectRepository(self._db),
            module_object_repository=ModuleObjectRepository(self._db),
        )

    def process(self):
        for item in self._event_objects:
            # fetch combined object and module object results
            rows: list[LatestObjectPerModuleResult | ObjectsTable] = (
                self._object_provider.list_all_objects_related_to_werkingsgebied(
                    werkingsgebied_code=getattr(item, "Code")
                )
            )

            related_objects = []
            related_module_objects = []

            for row in rows:
                match row:
                    case ObjectsTable():
                        related_objects.append(
                            DynamicObjectShort(
                                UUID=row.UUID,
                                Object_ID=row.Object_ID,
                                Object_Type=row.Object_Type,
                                Title=row.Title
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
                                Module_Title=row.module.Title
                            )
                        )

            result_objects = WerkingsgebiedRelatedObjects(
                Valid_Objects=related_objects,
                Module_Objects=related_module_objects
            )

            setattr(item, self._target_field, result_objects)

        return self._event_objects


class WerkingsgebiedRelatedObjectsListener(Listener[RetrievedObjectsEvent]):
    TARGET_FIELD: str = "Related_Objects"
    TARGET_SERVICE: str = "insert_computed_fields"

    def handle_event(self, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        if self.TARGET_SERVICE not in event.context.response_model.service_config:
            return event

        fields = event.context.response_model.service_config[self.TARGET_SERVICE]["fields"]
        if not any(field.get("field_name") == self.TARGET_FIELD for field in fields):
            return event

        service = WerkingsgebiedRelatedObjectService(event, self.TARGET_FIELD)
        result_rows = service.process()

        event.payload.rows = result_rows
        return event

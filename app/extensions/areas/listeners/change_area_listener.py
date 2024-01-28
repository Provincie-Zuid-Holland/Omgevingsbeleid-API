import uuid
from dataclasses import dataclass
from typing import List, Optional, Set

from sqlalchemy.orm import Session

from app.dynamic.config.models import DynamicObjectModel, Model
from app.dynamic.event.types import Listener
from app.extensions.areas.db.tables import AreasTable
from app.extensions.areas.dependencies import depends_area_geometry_repository, depends_area_repository
from app.extensions.areas.repository.area_geometry_repository import AreaGeometryRepository
from app.extensions.areas.repository.area_repository import AreaRepository
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.event.module_object_patched_event import ModuleObjectPatchedEvent
from app.extensions.source_werkingsgebieden.dependencies import depends_geometry_repository
from app.extensions.source_werkingsgebieden.repository.geometry_repository import GeometryRepository


@dataclass
class ChangeAreaConfig:
    fields: Set[str]


class AreaProcessor:
    def __init__(
        self,
        db: Session,
        config: ChangeAreaConfig,
        old_record: ModuleObjectsTable,
        new_record: ModuleObjectsTable,
        field_key: str,
    ):
        self._config: ChangeAreaConfig = config
        self._field_key: str = field_key
        self._db: Session = db
        self._old_record: ModuleObjectsTable = old_record
        self._new_record: ModuleObjectsTable = new_record
        self._old_field_value = getattr(old_record, field_key)
        self._new_field_value = getattr(new_record, field_key)
        self._source_geometry_repository: GeometryRepository = depends_geometry_repository(db)
        self._area_repository: AreaRepository = depends_area_repository(db)
        self._area_geometry_repository: AreaGeometryRepository = depends_area_geometry_repository(db)

    def process(self):
        if self._new_field_value is None:
            return self._new_record
        if self._old_field_value == self._new_field_value:
            return self._new_record

        # If the field value changes then it can either be the UUID of:
        # - The Source Werkingsgebieden
        # - An Area
        #
        # If it is the UUID of an Area then we do not need to do anything
        #
        # If it is the UUID of a Source Werkingsgebied then
        # we should fetch the Source Werkingsgebied to and fetch or create the Area based on it
        # And finally store the Area UUID back in to the record

        # The Area check
        area_table: Optional[AreasTable] = self._area_repository.get_by_uuid(self._new_field_value)
        if area_table is not None:
            return self._new_record

        # The Source Werkingsgebied check
        selected_werkingsgebied: dict = self._get_werkingsgebied(self._new_field_value)
        area_uuid: uuid.UUID = self._get_or_create_area(selected_werkingsgebied)
        setattr(self._new_record, self._field_key, area_uuid)

        return self._new_record

    def _get_werkingsgebied(self, werkingsgebied_uuid: uuid.UUID) -> dict:
        selected_werkingsgebied: Optional[dict] = self._source_geometry_repository.get_werkingsgebied_optional(
            werkingsgebied_uuid
        )
        if selected_werkingsgebied is None:
            raise ValueError("Invalid UUID for Werkingsgebied")

        return selected_werkingsgebied

    def _get_or_create_area(self, werkingsgebied: dict) -> uuid.UUID:
        werkingsgebied_uuid: uuid.UUID = uuid.UUID(werkingsgebied["UUID"])
        existing_area: Optional[AreasTable] = self._area_repository.get_by_werkingsgebied_uuid(werkingsgebied_uuid)
        if existing_area is not None:
            return existing_area.UUID

        area_uuid: uuid.UUID = uuid.uuid4()
        self._area_geometry_repository.create_area(
            uuidx=area_uuid,
            werkingsgebied=werkingsgebied,
            created_date=self._new_record.Modified_Date,
            created_by_uuid=self._new_record.Modified_By_UUID,
        )

        return area_uuid


class ChangeAreaListener(Listener[ModuleObjectPatchedEvent]):
    def handle_event(self, event: ModuleObjectPatchedEvent) -> Optional[ModuleObjectPatchedEvent]:
        config: Optional[ChangeAreaConfig] = self._collect_config(event.context.request_model)
        if not config:
            return event

        changed_fields: Set[str] = set(event.context.changes.keys())
        interested_fields: Set[str] = set.intersection(config.fields, changed_fields)
        if not interested_fields:
            return event

        db: Session = event.get_db()
        new_record: ModuleObjectsTable = event.payload.new_record
        for field in interested_fields:
            extractor: AreaProcessor = AreaProcessor(
                db,
                config,
                event.context.old_record,
                new_record,
                field,
            )
            new_record = extractor.process()

        event.payload.new_record = new_record
        return event

    def _collect_config(self, request_model: Model) -> Optional[ChangeAreaConfig]:
        if not isinstance(request_model, DynamicObjectModel):
            return None
        if not "change_area" in request_model.service_config:
            return None

        config_dict: dict = request_model.service_config.get("change_area", {})
        fields: List[str] = []
        for field in config_dict.get("fields", []):
            if not isinstance(field, str):
                raise RuntimeError("Invalid change_area config, expect `fields` to be a list of strings")
            fields.append(field)
        if not fields:
            return None

        config: ChangeAreaConfig = ChangeAreaConfig(fields=set(fields))
        return config

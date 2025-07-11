import uuid
from typing import Optional, Set

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.domains.werkingsgebieden.repositories.area_geometry_repository import AreaGeometryRepository
from app.api.domains.werkingsgebieden.repositories.area_repository import AreaRepository
from app.api.domains.werkingsgebieden.repositories.geometry_repository import GeometryRepository
from app.core.tables.modules import ModuleObjectsTable
from app.core.tables.others import AreasTable


class AreaProcessorConfig(BaseModel):
    fields: Set[str] = Field(default_factory=set)


class AreaProcessorService:
    def __init__(
        self,
        session: Session,
        source_geometry_repository: GeometryRepository,
        area_repository: AreaRepository,
        area_geometry_repository: AreaGeometryRepository,
        config: AreaProcessorConfig,
    ):
        self._session: Session = session
        self._source_geometry_repository: GeometryRepository = source_geometry_repository
        self._area_repository: AreaRepository = area_repository
        self._area_geometry_repository: AreaGeometryRepository = area_geometry_repository
        self._config: AreaProcessorConfig = config

    def process(self, old_recold: ModuleObjectsTable, new_record: ModuleObjectsTable) -> ModuleObjectsTable:
        for field_key in self._config.fields:
            new_record = self._process_field(old_recold, new_record, field_key)

        return new_record

    def _process_field(
        self, old_recold: ModuleObjectsTable, new_record: ModuleObjectsTable, field_key: str
    ) -> ModuleObjectsTable:
        old_field_value = getattr(old_recold, field_key)
        new_field_value = getattr(new_record, field_key)

        if new_field_value is None:
            return new_record
        if old_field_value == new_field_value:
            return new_record

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
        area_table: Optional[AreasTable] = self._area_repository.get_by_uuid(self._session, new_field_value)
        if area_table is not None:
            return new_record

        # The Source Werkingsgebied check
        selected_werkingsgebied: dict = self._get_werkingsgebied(new_field_value)
        area_uuid: uuid.UUID = self._get_or_create_area(new_record, selected_werkingsgebied)
        setattr(new_record, field_key, area_uuid)

        return new_record

    def _get_werkingsgebied(self, werkingsgebied_uuid: uuid.UUID) -> dict:
        selected_werkingsgebied: Optional[dict] = self._source_geometry_repository.get_werkingsgebied_optional(
            self._session,
            werkingsgebied_uuid,
        )
        if selected_werkingsgebied is None:
            raise ValueError("Invalid UUID for Werkingsgebied")

        return selected_werkingsgebied

    def _get_or_create_area(self, new_record: ModuleObjectsTable, werkingsgebied: dict) -> uuid.UUID:
        werkingsgebied_uuid: uuid.UUID = uuid.UUID(werkingsgebied["UUID"])
        existing_area: Optional[AreasTable] = self._area_repository.get_by_werkingsgebied_uuid(
            self._session, werkingsgebied_uuid
        )
        if existing_area is not None:
            return existing_area.UUID

        area_uuid: uuid.UUID = uuid.uuid4()
        self._area_geometry_repository.create_area(
            session=self._session,
            uuidx=area_uuid,
            werkingsgebied=werkingsgebied,
            created_date=new_record.Modified_Date,
            created_by_uuid=new_record.Modified_By_UUID,
        )

        return area_uuid


class AreaProcessorServiceFactory:
    def __init__(
        self,
        source_geometry_repository: GeometryRepository,
        area_repository: AreaRepository,
        area_geometry_repository: AreaGeometryRepository,
    ):
        self._source_geometry_repository: GeometryRepository = source_geometry_repository
        self._area_repository: AreaRepository = area_repository
        self._area_geometry_repository: AreaGeometryRepository = area_geometry_repository

    def create_service(
        self,
        session: Session,
        config: AreaProcessorConfig,
    ) -> AreaProcessorService:
        return AreaProcessorService(
            session,
            self._source_geometry_repository,
            self._area_repository,
            self._area_geometry_repository,
            config,
        )

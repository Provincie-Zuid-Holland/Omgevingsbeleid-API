from typing import List, Optional, Set, Union
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.objects.repositories.asset_repository import AssetRepository
from app.api.events.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.api.events.retrieved_objects_event import RetrievedObjectsEvent
from app.core.services.event.types import Listener
from app.core.tables.others import AssetsTable
from app.core.types import DynamicObjectModel, Model


class GetImagesConfig(BaseModel):
    fields: Set[str]


class ImageInserter:
    def __init__(
        self,
        session: Session,
        asset_repository: AssetRepository,
        event: Union[RetrievedModuleObjectsEvent, RetrievedObjectsEvent],
        config: GetImagesConfig,
    ):
        self._session: Session = session
        self._asset_repository: AssetRepository = asset_repository
        self._config: GetImagesConfig = config
        self._rows: List[BaseModel] = event.payload.rows

    def process(self) -> List[BaseModel]:
        for index, row in enumerate(self._rows):
            for field_name in self._config.fields:
                if not hasattr(row, field_name):
                    continue

                content: str = getattr(row, field_name)
                if not content:
                    continue

                try:
                    image_uuid = UUID(content)
                except ValueError:
                    continue

                asset: Optional[AssetsTable] = self._asset_repository.get_by_uuid(self._session, image_uuid)
                if not asset:
                    continue

                setattr(row, field_name, asset.Content)

        return self._rows


class ImageInserterFactory:
    def __init__(self, asset_repository: AssetRepository):
        self._asset_repository: AssetRepository = asset_repository

    def create(
        self,
        session: Session,
        event: Union[RetrievedModuleObjectsEvent, RetrievedObjectsEvent],
        config: GetImagesConfig,
    ) -> ImageInserter:
        return ImageInserter(
            session,
            self._asset_repository,
            event,
            config,
        )


class GetImagesForModuleListener(Listener[RetrievedModuleObjectsEvent]):
    def __init__(self, service_factory: ImageInserterFactory):
        self._service_factory: ImageInserterFactory = service_factory

    def handle_event(
        self, session: Session, event: RetrievedModuleObjectsEvent
    ) -> Optional[RetrievedModuleObjectsEvent]:
        config: Optional[GetImagesConfig] = self._collect_config(event.context.response_model)
        if not config:
            return event
        if not config.fields:
            return event

        inserter: ImageInserter = self._service_factory.create(session, event, config)
        result_rows = inserter.process()

        event.payload.rows = result_rows
        return event

    def _collect_config(self, request_model: Model) -> Optional[GetImagesConfig]:
        if not isinstance(request_model, DynamicObjectModel):
            return None
        if not "get_image" in request_model.service_config:
            return None

        config_dict: dict = request_model.service_config.get("get_image", {})
        fields: List[str] = []
        for field in config_dict.get("fields", []):
            if not isinstance(field, str):
                raise RuntimeError("Invalid get_image config, expect `fields` to be a list of strings")
            fields.append(field)
        if not fields:
            return None

        config: GetImagesConfig = GetImagesConfig(fields=set(fields))
        return config


class GetImagesForObjectListener(Listener[RetrievedObjectsEvent]):
    def __init__(self, service_factory: ImageInserterFactory):
        self._service_factory: ImageInserterFactory = service_factory

    def handle_event(self, session: Session, event: RetrievedObjectsEvent) -> Optional[RetrievedObjectsEvent]:
        config: Optional[GetImagesConfig] = self._collect_config(event.context.response_model)
        if not config:
            return event
        if not config.fields:
            return event

        inserter: ImageInserter = self._service_factory.create(session, event, config)
        result_rows = inserter.process()

        event.payload.rows = result_rows
        return event

    def _collect_config(self, request_model: Model) -> Optional[GetImagesConfig]:
        if not isinstance(request_model, DynamicObjectModel):
            return None
        if not "get_image" in request_model.service_config:
            return None

        config_dict: dict = request_model.service_config.get("get_image", {})
        fields: List[str] = []
        for field in config_dict.get("fields", []):
            if not isinstance(field, str):
                raise RuntimeError("Invalid get_image config, expect `fields` to be a list of strings")
            fields.append(field)
        if not fields:
            return None

        config: GetImagesConfig = GetImagesConfig(fields=set(fields))
        return config

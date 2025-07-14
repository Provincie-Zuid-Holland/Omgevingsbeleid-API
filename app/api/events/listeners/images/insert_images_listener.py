import re
from typing import Generic, List, Optional, Set, TypeVar
from uuid import UUID

from bs4 import BeautifulSoup
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.domains.objects.repositories.asset_repository import AssetRepository
from app.api.events.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.api.events.retrieved_objects_event import RetrievedObjectsEvent
from app.core.services.event.types import Event, Listener
from app.core.tables.others import AssetsTable
from app.core.types import DynamicObjectModel, Model


class InsertHtmlImagesConfig(BaseModel):
    fields: Set[str]


class HtmlImagesInserter:
    def __init__(
        self,
        session: Session,
        asset_repository: AssetRepository,
        rows: List[BaseModel],
        config: InsertHtmlImagesConfig,
    ):
        self._session: Session = session
        self._config: InsertHtmlImagesConfig = config
        self._rows: List[BaseModel] = rows
        self._asset_repository: AssetRepository = asset_repository

    def process(self) -> List[BaseModel]:
        for index, row in enumerate(self._rows):
            for field_name in self._config.fields:
                if not hasattr(row, field_name):
                    continue

                content: str = getattr(row, field_name)
                if not isinstance(content, str):
                    continue

                soup = BeautifulSoup(content, "html.parser")

                for img in soup.find_all("img", src=re.compile(r"^\[ASSET")):
                    try:
                        asset_uuid = UUID(img["src"].split(":")[1][:-1])
                    except ValueError:
                        continue

                    asset: Optional[AssetsTable] = self._asset_repository.get_by_uuid(self._session, asset_uuid)
                    if not asset:
                        continue

                    img["src"] = asset.Content

                setattr(row, field_name, str(soup))

        return self._rows


class HtmlImagesInserterFactory:
    def __init__(self, asset_repository: AssetRepository):
        self._asset_repository: AssetRepository = asset_repository

    def create(
        self,
        session: Session,
        rows: List[BaseModel],
        config: InsertHtmlImagesConfig,
    ) -> HtmlImagesInserter:
        return HtmlImagesInserter(
            session=session,
            asset_repository=self._asset_repository,
            rows=rows,
            config=config,
        )


EventT = TypeVar("EventT", bound=Event)


class InsertHtmlImagesListenerBase(Listener[EventT], Generic[EventT]):
    def __init__(self, service_factory: HtmlImagesInserterFactory):
        self._service_factory: HtmlImagesInserterFactory = service_factory

    def handle_event(self, session: Session, event: EventT) -> Optional[EventT]:
        config: Optional[InsertHtmlImagesConfig] = self._collect_config(event.context.response_model)
        if not config or not config.fields:
            return event

        inserter: HtmlImagesInserter = self._service_factory.create(session, event.payload.rows, config)
        result_rows = inserter.process()

        event.payload.rows = result_rows
        return event

    def _collect_config(self, request_model: Model) -> Optional[InsertHtmlImagesConfig]:
        if not isinstance(request_model, DynamicObjectModel):
            return None
        if not "insert_assets" in request_model.service_config:
            return None

        config_dict: dict = request_model.service_config.get("insert_assets", {})
        fields: List[str] = []
        for field in config_dict.get("fields", []):
            if not isinstance(field, str):
                raise RuntimeError("Invalid insert_assets config, expect `fields` to be a list of strings")
            fields.append(field)
        if not fields:
            return None

        config: InsertHtmlImagesConfig = InsertHtmlImagesConfig(fields=set(fields))
        return config


class InsertHtmlImagesForModuleListener(InsertHtmlImagesListenerBase[RetrievedModuleObjectsEvent]):
    pass


class InsertHtmlImagesForObjectListener(InsertHtmlImagesListenerBase[RetrievedObjectsEvent]):
    pass

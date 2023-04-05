from typing import List, Set, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict
from pydantic import BaseModel

from sqlalchemy import desc, func, select, or_
from sqlalchemy.orm import Session
from app.dynamic.db.objects_table import ObjectsTable

from app.dynamic.event.types import Listener
from app.dynamic.event.retrieved_objects_event import RetrievedObjectsEvent
from app.dynamic.config.models import DynamicObjectModel
from app.dynamic.converter import Converter
from app.extensions.modules.event.retrieved_module_objects_event import RetrievedModuleObjectsEvent
from app.extensions.relations.db.tables import RelationsTable
from app.extensions.relations.service.add_relations import AddRelationsService


class RetrievedModuleObjectsListener(Listener[RetrievedModuleObjectsEvent]):
    def __init__(self, converter: Converter):
        self._converter: Converter = converter

    def handle_event(self, event: RetrievedModuleObjectsEvent) -> RetrievedModuleObjectsEvent:
        add_service: AddRelationsService = AddRelationsService(
            self._converter,
            event.get_db(),
            event.payload.rows,
            event.context.response_model,
        )

        result_rows: List[BaseModel] = add_service.add_relations()
        event.payload.rows = result_rows

        return event

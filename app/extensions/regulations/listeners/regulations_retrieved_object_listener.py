from typing import List, Optional
from dataclasses import dataclass
from collections import defaultdict
from sqlalchemy import select

from sqlalchemy.orm import Session
from app.core.utils.utils import table_to_dict

from app.dynamic.event.types import Listener
from app.dynamic.event.retrieved_objects_event import RetrievedObjectsEvent
from app.dynamic.config.models import DynamicObjectModel
from app.extensions.regulations.db.tables import (
    ObjectRegulationsTable,
    RegulationsTable,
)


@dataclass
class Config:
    object_codes: List[str]
    to_field: str


class RegulationsRetrievedObjectsListener(Listener[RetrievedObjectsEvent]):
    def handle_event(self, event: RetrievedObjectsEvent) -> RetrievedObjectsEvent:
        config: Optional[Config] = self._collect_config(event)
        if not config:
            return event

        regulations_rows: List[dict] = self._fetch_regulations(event.get_db(), config)

        """
        regulations=
        {
            # target/to (owner)
            'ambitie-1': {
                # object-type of the relation
                # used to map to the right field in the target
                'Regulations': [
                    {row},
                    {row},
                ],
            }
        }
        """
        regulations = defaultdict(lambda: defaultdict(list))
        for regulation_row in regulations_rows:
            object_code: str = regulation_row.get("Object_Code")
            regulations[object_code][config.to_field].append(regulation_row)

        # Now we union the regulation "rows" into the event rows
        result_rows: List[dict] = []
        for row in event.payload.rows:
            if getattr(row, "Code") in regulations:
                for field_name, content in regulations[getattr(row, "Code")].items():
                    setattr(row, field_name, content)
            result_rows.append(row)

        event.payload.rows = result_rows

        return event

    def _fetch_regulations(self, db: Session, config: Config) -> List[dict]:
        stmt = (
            select(RegulationsTable, ObjectRegulationsTable.Object_Code)
            .select_from(ObjectRegulationsTable)
            .join(RegulationsTable)
            .filter(ObjectRegulationsTable.Object_Code.in_(config.object_codes))
        )
        rows = db.execute(stmt).all()
        dict_rows = [r._asdict() for r in rows]
        dict_rows = []
        for row in rows:
            regulations_table, object_code = row
            dict_row = table_to_dict(regulations_table)
            dict_row["Object_Code"] = object_code
            dict_rows.append(dict_row)

        return dict_rows

    def _collect_config(self, event: RetrievedObjectsEvent) -> Optional[Config]:
        if not isinstance(event.context.response_model, DynamicObjectModel):
            return None

        if not "regulations" in event.context.response_model.service_config:
            return None

        object_codes: List[str] = list(
            set([getattr(r, "Code") for r in event.payload.rows])
        )
        config_dict: dict = event.context.response_model.service_config.get(
            "regulations"
        )
        to_field: str = config_dict.get("to_field")

        return Config(
            object_codes,
            to_field,
        )

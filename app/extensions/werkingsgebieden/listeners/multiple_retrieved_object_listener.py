from typing import List, Optional
from dataclasses import dataclass
from collections import defaultdict
from sqlalchemy import select

from sqlalchemy.orm import Session
from app.core.utils.utils import table_to_dict

from app.dynamic.event.types import Listener
from app.dynamic.event.retrieved_objects_event import RetrievedObjectsEvent
from app.dynamic.config.models import DynamicObjectModel
from app.extensions.werkingsgebieden.db.tables import (
    ObjectWerkingsgebiedenTable,
    WerkingsgebiedenTable,
)


@dataclass
class Config:
    object_codes: List[str]
    to_field: str


class MultipleRetrievedObjectsListener(Listener[RetrievedObjectsEvent]):
    def handle_event(self, event: RetrievedObjectsEvent) -> RetrievedObjectsEvent:
        config: Optional[Config] = self._collect_config(event)
        if not config:
            return event

        werkingsgebieden_rows: List[dict] = self._fetch_werkingsgebieden(
            event.get_db(), config
        )

        """
        Same trick as in the relations extension
        werkingsgebieden=
        {
            # target/to (owner)
            'ambitie-1': {
                # object-type of the relation
                # used to map to the right field in the target
                'Werkingsgebieden': [
                    {row},
                    {row},
                ],
            }
        }
        """
        werkingsgebieden = defaultdict(lambda: defaultdict(list))
        for werkingsgebied_row in werkingsgebieden_rows:
            object_code: str = werkingsgebied_row.get("Object_Code")
            werkingsgebieden[object_code][config.to_field].append(werkingsgebied_row)

        # Now we union the relation "rows" into the event rows
        result_rows: List[dict] = []
        for row in event.payload.rows:
            if row.get("Code") in werkingsgebieden:
                row = row | dict(werkingsgebieden[row.get("Code")])
            result_rows.append(row)

        event.payload.rows = result_rows

        return event

    def _fetch_werkingsgebieden(self, db: Session, config: Config) -> List[dict]:
        stmt = (
            select(WerkingsgebiedenTable, ObjectWerkingsgebiedenTable.Object_Code)
            .select_from(ObjectWerkingsgebiedenTable)
            .join(WerkingsgebiedenTable)
            .filter(ObjectWerkingsgebiedenTable.Object_Code.in_(config.object_codes))
        )
        rows = db.execute(stmt).all()
        dict_rows = [r._asdict() for r in rows]
        dict_rows = []
        for row in rows:
            werkingsgebieden_table, object_code = row
            dict_row = table_to_dict(werkingsgebieden_table)
            dict_row["Object_Code"] = object_code
            dict_rows.append(dict_row)

        return dict_rows

    def _collect_config(self, event: RetrievedObjectsEvent) -> Optional[Config]:
        if not isinstance(event.context.response_model, DynamicObjectModel):
            return None

        if not "werkingsgebieden" in event.context.response_model.service_config:
            return None

        object_codes: List[str] = list(set([r.get("Code") for r in event.payload.rows]))

        config_dict: dict = event.context.response_model.service_config.get(
            "werkingsgebieden"
        )
        to_field: str = config_dict.get("to_field")

        return Config(
            object_codes,
            to_field,
        )

from typing import List, Set, Dict
from dataclasses import dataclass
from sqlalchemy import select

from sqlalchemy.orm import Session
from app.core.utils.utils import table_to_dict

from app.dynamic.event.types import Listener
from app.dynamic.event.retrieved_objects_event import RetrievedObjectsEvent
from app.dynamic.config.models import Model, DynamicObjectModel
from app.extensions.werkingsgebieden.db.tables import WerkingsgebiedenTable


@dataclass
class FieldMap:
    from_field: str
    to_field: str


class SingleRetrievedObjectsListener(Listener[RetrievedObjectsEvent]):
    def handle_event(self, event: RetrievedObjectsEvent) -> RetrievedObjectsEvent:
        field_map: List[FieldMap] = self._collect_field_map(
            event.context.response_model
        )
        if not field_map:
            return event

        from_field_keys: Set[str] = set([f.from_field for f in field_map])

        werkingsgebieden_uuids: Set[str] = set()
        for row in event.payload.rows:
            for key in from_field_keys:
                werkingsgebieden_uuids.add(row[key])

        werkingsgebieden_map: Dict[str, dict] = self._fetch_werkingsgebieden(
            event.get_db(), werkingsgebieden_uuids
        )

        # Fill the to_field for each row with the correct werkingsgebied
        for row_key, _ in enumerate(event.payload.rows):
            for field in field_map:
                # Check if the werkingsgebied exists
                werkingsgebied_uuid: str = event.payload.rows[row_key][field.from_field]
                if not werkingsgebied_uuid in werkingsgebieden_map:
                    continue

                event.payload.rows[row_key][field.to_field] = werkingsgebieden_map[
                    werkingsgebied_uuid
                ]

        return event

    def _fetch_werkingsgebieden(self, db: Session, uuids: Set[str]) -> Dict[str, dict]:
        if not uuids:
            return {}

        stmt = select(WerkingsgebiedenTable).filter(
            WerkingsgebiedenTable.UUID.in_(uuids)
        )
        rows = db.scalars(stmt).all()
        werkingsgebied_map = {r.UUID: table_to_dict(r) for r in rows}
        return werkingsgebied_map

    def _collect_field_map(self, response_model: Model) -> List[FieldMap]:
        if not isinstance(response_model, DynamicObjectModel):
            return []

        if not "werkingsgebied" in response_model.service_config:
            return []

        result: List[FieldMap] = []
        fields_map_config: List[dict] = response_model.service_config.get(
            "werkingsgebied"
        ).get("fields_map")
        for field_map_config in fields_map_config:
            from_field: str = field_map_config.get("from_field")
            to_field: str = field_map_config.get("to_field")

            result.append(
                FieldMap(
                    from_field,
                    to_field,
                )
            )

        return result

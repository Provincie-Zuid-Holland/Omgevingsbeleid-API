from typing import List, Set, Dict
from dataclasses import dataclass
from uuid import UUID
from sqlalchemy import select

from sqlalchemy.orm import Session

from app.dynamic.event.types import Listener
from app.dynamic.event.retrieved_objects_event import RetrievedObjectsEvent
from app.dynamic.config.models import Model, DynamicObjectModel
from app.extensions.users.db.tables import UsersTable


@dataclass
class FieldMap:
    from_field: str
    to_field: str


class RetrievedObjectsListener(Listener[RetrievedObjectsEvent]):
    def handle_event(self, event: RetrievedObjectsEvent) -> RetrievedObjectsEvent:
        field_map: List[FieldMap] = self._collect_field_map(
            event.context.response_model
        )
        if not field_map:
            return event

        from_field_keys: Set[str] = set([f.from_field for f in field_map])

        user_uuids: Set[UUID] = set()
        for row in event.payload.rows:
            for key in from_field_keys:
                user_uuids.add(row[key])

        user_map: Dict[str, dict] = self._fetch_users(event.get_db(), user_uuids)

        # Fill the to_field for each row with the correct user
        for row_key, _ in enumerate(event.payload.rows):
            for field in field_map:
                # Check if the user exists
                user_uuid: str = event.payload.rows[row_key][field.from_field]
                if not user_uuid in user_map:
                    continue

                event.payload.rows[row_key][field.to_field] = user_map[user_uuid]

        return event

    def _fetch_users(self, db: Session, uuids: Set[UUID]) -> Dict[str, dict]:
        if not uuids:
            return {}

        stmt = select(UsersTable).filter(UsersTable.UUID.in_(uuids))

        user_map = {}
        for user in db.scalars(stmt).all():
            user_map[user.UUID] = {
                "UUID": user.UUID,
                "Gebruikersnaam": user.Gebruikersnaam,
                "Email": user.Email,
                "Rol": user.Rol,
                "IsActief": user.IsActief,
            }

        return user_map

    def _collect_field_map(self, response_model: Model) -> List[FieldMap]:
        if not isinstance(response_model, DynamicObjectModel):
            return []

        if not "extended_user" in response_model.service_config:
            return []

        result: List[FieldMap] = []
        fields_map_config: List[dict] = response_model.service_config.get(
            "extended_user"
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

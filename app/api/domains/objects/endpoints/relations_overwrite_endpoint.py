import json
from datetime import datetime, timezone
from typing import Annotated, List, Sequence

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.api.api_container import ApiContainer
from app.api.domains.objects.types import WriteRelation
from app.api.domains.users.dependencies import depends_current_user
from app.api.endpoint import BaseEndpointContext
from app.api.types import ResponseOK
from app.core.tables.others import ChangeLogTable, RelationsTable
from app.core.tables.users import UsersTable


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        allowed_object_types_relations: List[str],
        object_type: str,
        object_id: int,
        overwrite_list: List[WriteRelation],
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._object_type: str = object_type
        self._object_id: int = object_id
        self._object_code: str = f"{object_type}-{object_id}"
        self._overwrite_list: List[WriteRelation] = overwrite_list
        self._allowed_object_types_relations: List[str] = allowed_object_types_relations

    def handle(self) -> ResponseOK:
        self._guard_invalid_relations()
        try:
            self._log_action()

            self._remove_current_relations()
            self._create_relations()
            self._db.commit()

            return ResponseOK(message="OK")
        except Exception as e:
            self._db.rollback()
            raise e

    def _guard_invalid_relations(self):
        for relation in self._overwrite_list:
            if relation.Object_Type not in self._allowed_object_types_relations:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f"Invalid object_type for relation with '{self._object_code}'"
                )

    def _log_action(self):
        action_data: str = json.dumps([l.model_dump() for l in self._overwrite_list])
        current_relations: List[dict] = self._fetch_current_relations()
        before_data: str = json.dumps(current_relations)

        after: List[dict] = [
            RelationsTable.create(
                data.Description,
                self._object_code,
                data.Code,
            ).to_dict()
            for data in self._overwrite_list
        ]
        after_data: str = json.dumps(after)

        change_log = ChangeLogTable(
            Object_Type=self._object_type,
            Object_ID=self._object_id,
            Created_Date=datetime.now(timezone.utc),
            Created_By_UUID=self._user.UUID,
            Action_Type="overwrite_relations",
            Action_Data=action_data,
            Before=before_data,
            After=after_data,
        )
        self._db.add(change_log)

    def _fetch_current_relations(self):
        stmt = select(RelationsTable).filter(
            or_(
                RelationsTable.From_Code == self._object_code,
                RelationsTable.To_Code == self._object_code,
            )
        )
        rows: Sequence[RelationsTable] = self._db.scalars(stmt).all()
        dict_rows: List[dict] = [r.to_dict() for r in rows]
        return dict_rows

    def _remove_current_relations(self):
        stmt = delete(RelationsTable).filter(
            or_(
                RelationsTable.From_Code == self._object_code,
                RelationsTable.To_Code == self._object_code,
            )
        )
        self._db.execute(stmt)

    def _create_relations(self):
        if not self._overwrite_list:
            return

        for data in self._overwrite_list:
            relation: RelationsTable = RelationsTable.create(
                data.Description,
                self._object_code,
                data.Code,
            )
            self._db.add(relation)


class RelationsOverwriteEndpointContext(BaseEndpointContext):
    object_type: str
    allowed_object_types_relations: List[str]


@inject
def post_relations_overwrite_endpoint(
    lineage_id: int,
    overwrite_list: List[WriteRelation],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    db: Annotated[Session, Depends(Provide[ApiContainer.db])],
    context: Annotated[RelationsOverwriteEndpointContext, Depends()],
) -> ResponseOK:
    handler: EndpointHandler = EndpointHandler(
        db,
        user,
        context.allowed_object_types_relations,
        context.object_type,
        lineage_id,
        overwrite_list,
    )
    return handler.handle()

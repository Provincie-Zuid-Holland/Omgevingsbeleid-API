import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.converter import Converter
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.change_logger.db.tables import ChangeLogTable
from app.extensions.relations.db.tables import RelationsTable
from app.extensions.relations.models.models import WriteRelationShort
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        allowed_object_types_relations: List[str],
        object_type: str,
        object_id: str,
        overwrite_list: List[WriteRelationShort],
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._object_type: str = object_type
        self._object_id: int = object_id
        self._object_code: str = f"{object_type}-{object_id}"
        self._overwrite_list: List[WriteRelationShort] = overwrite_list
        self._allowed_object_types_relations: List[str] = allowed_object_types_relations

    def handle(self) -> ResponseOK:
        self._guard_invalid_relations()
        try:
            self._log_action()

            self._remove_current_relations()
            self._create_relations()
            self._db.commit()

            return ResponseOK(
                message="OK",
            )
        except Exception as e:
            self._db.rollback()
            raise e

    def _guard_invalid_relations(self):
        for relation in self._overwrite_list:
            if relation.Object_Type not in self._allowed_object_types_relations:
                raise ValueError(f"Invalid object_type for relation with '@TODO object-id'")

    def _log_action(self):
        action_data: str = json.dumps([l.dict() for l in self._overwrite_list])
        current_relations: List[dict] = self._fetch_current_relations()
        before_data: str = json.dumps(current_relations)

        after: List[RelationsTable] = [
            RelationsTable.create(
                data.Description,
                self._object_code,
                data.Code,
            ).to_dict()
            for data in self._overwrite_list
        ]
        after_data: str = json.dumps(after)

        change_log: ChangeLogTable = ChangeLogTable(
            Object_Type=self._object_type,
            Object_ID=self._object_id,
            Created_Date=datetime.utcnow(),
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
        rows: List[RelationsTable] = self._db.scalars(stmt).all()
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


class OverwriteRelationsEndpoint(Endpoint):
    def __init__(
        self,
        path: str,
        object_type: str,
        allowed_object_types_relations: List[str],
    ):
        self._path: str = path
        self._object_type: str = object_type
        self._allowed_object_types_relations: List[str] = allowed_object_types_relations

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            lineage_id: int,
            overwrite_list: List[WriteRelationShort],
            user: UsersTable = Depends(depends_current_active_user),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                self._allowed_object_types_relations,
                self._object_type,
                lineage_id,
                overwrite_list,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["PUT"],
            response_model=ResponseOK,
            summary=f"Overwrite all relations of the given {self._object_type} lineage",
            description=None,
            tags=[self._object_type],
        )

        return router


class OverwriteRelationsEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "overwrite_relations"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data

        # Confirm that path arguments are present
        path: str = endpoint_config.prefix + resolver_config.get("path", "")
        if not "{lineage_id}" in path:
            raise RuntimeError("Missing {lineage_id} argument in path")

        # You can not use this endpoint if you do not specify relations
        allowed_object_types_relations: List[str] = resolver_config.get("allowed_object_types_relations", [])
        if not allowed_object_types_relations:
            raise RuntimeError("Missing required config allowed_object_types_relations")

        return OverwriteRelationsEndpoint(
            path=path,
            object_type=api.object_type,
            allowed_object_types_relations=allowed_object_types_relations,
        )

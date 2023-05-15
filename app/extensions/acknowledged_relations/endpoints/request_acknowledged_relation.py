from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from app.core.dependencies import depends_db

from app.dynamic.endpoints.endpoint import EndpointResolver, Endpoint
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.event_dispatcher import EventDispatcher
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.converter import Converter
from app.dynamic.utils.response import ResponseOK
from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationsTable
from app.extensions.acknowledged_relations.models.models import (
    AcknowledgedRelationSide,
    RequestAcknowledgedRelation,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        user: UsersTable,
        object_type: str,
        lineage_id: int,
        allowed_object_types: List[str],
        object_in: RequestAcknowledgedRelation,
    ):
        self._db: Session = db
        self._user: UsersTable = user
        self._object_type: str = object_type
        self._lineage_id: int = lineage_id
        self._allowed_object_types: List[str] = allowed_object_types
        self._object_in: RequestAcknowledgedRelation = object_in
        self._now: datetime = datetime.now()

    def handle(self) -> ResponseOK:
        if self._object_in.Object_Type not in self._allowed_object_types:
            raise HTTPException(400, "Invalid Object_Type")

        my_side = AcknowledgedRelationSide(
            Object_ID=self._lineage_id,
            Object_Type=self._object_type,
            Acknowledged=self._now,
            Acknowledged_By_UUID=self._user.UUID,
            Explanation=self._object_in.Explanation,
        )
        their_side = AcknowledgedRelationSide(
            Object_ID=self._object_in.Object_ID,
            Object_Type=self._object_in.Object_Type,
        )

        ack_table: AcknowledgedRelationsTable = AcknowledgedRelationsTable(
            Requested_By_Code=my_side.Code,
            Created_Date=self._now,
            Created_By_UUID=self._user.UUID,
            Modified_Date=self._now,
            Modified_By_UUID=self._user.UUID,
        )
        ack_table.with_sides(my_side, their_side)

        active_relation = (
            self._db.query(AcknowledgedRelationsTable)
            .filter(
                and_(
                    AcknowledgedRelationsTable.Requested_By_Code == ack_table.Requested_By_Code,
                    AcknowledgedRelationsTable.From_Code == ack_table.From_Code,
                    AcknowledgedRelationsTable.To_Code == ack_table.To_Code,
                    AcknowledgedRelationsTable.Denied.is_(None),
                    AcknowledgedRelationsTable.Deleted_At.is_(None),
                )
            )
            .first()
        )

        if active_relation:
            raise HTTPException(
                status_code=409, detail="Existing relation(request), either edit or delete first"
            )

        # Query for max version so we can increment by 1
        max_version = self._db.query(func.max(AcknowledgedRelationsTable.Version)).filter(
            and_(
                AcknowledgedRelationsTable.Requested_By_Code == ack_table.Requested_By_Code,
                AcknowledgedRelationsTable.From_Code == ack_table.From_Code,
                AcknowledgedRelationsTable.To_Code == ack_table.To_Code,
            )
        ).scalar()

        if max_version is not None:
            ack_table.Version = max_version + 1

        self._db.add(ack_table)
        self._db.flush()
        self._db.commit()

        return ResponseOK(message="OK")


class RequestAcknowledgedRelationEndpoint(Endpoint):
    def __init__(
        self,
        event_dispatcher: EventDispatcher,
        path: str,
        object_type: str,
        allowed_object_types: List[str],
    ):
        self._event_dispatcher: EventDispatcher = event_dispatcher
        self._path: str = path
        self._object_type: str = object_type
        self._allowed_object_types: List[str] = allowed_object_types

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            lineage_id: int,
            object_in: RequestAcknowledgedRelation,
            user: UsersTable = Depends(depends_current_active_user),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                user,
                self._object_type,
                lineage_id,
                self._allowed_object_types,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Request an acknowledged relation to another object",
            description=None,
            tags=[self._object_type],
        )

        return router


class RequestAcknowledgedRelationEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "request_acknowledged_relation"

    def generate_endpoint(
        self,
        event_dispatcher: EventDispatcher,
        converter: Converter,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        allowed_object_types: List[str] = resolver_config.get("allowed_object_types", [])
        if not allowed_object_types:
            raise RuntimeError("Missing required config allowed_object_types")

        return RequestAcknowledgedRelationEndpoint(
            event_dispatcher=event_dispatcher,
            path=path,
            object_type=api.object_type,
            allowed_object_types=allowed_object_types,
        )

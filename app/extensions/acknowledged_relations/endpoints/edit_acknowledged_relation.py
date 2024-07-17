from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import depends_db
from app.dynamic.config.models import Api, EndpointConfig
from app.dynamic.endpoints.endpoint import Endpoint, EndpointResolver
from app.dynamic.models_resolver import ModelsResolver
from app.dynamic.utils.response import ResponseOK
from app.extensions.acknowledged_relations.db.tables import AcknowledgedRelationsTable
from app.extensions.acknowledged_relations.dependencies import depends_acknowledged_relations_repository
from app.extensions.acknowledged_relations.models.models import AcknowledgedRelationSide, EditAcknowledgedRelation
from app.extensions.acknowledged_relations.repository.acknowledged_relations_repository import (
    AcknowledgedRelationsRepository,
)
from app.extensions.users.db.tables import UsersTable
from app.extensions.users.dependencies import depends_current_active_user


class EndpointHandler:
    def __init__(
        self,
        db: Session,
        repository: AcknowledgedRelationsRepository,
        user: UsersTable,
        object_type: str,
        lineage_id: int,
        object_in: EditAcknowledgedRelation,
    ):
        self._db: Session = db
        self._repository: AcknowledgedRelationsRepository = repository
        self._user: UsersTable = user
        self._object_type: str = object_type
        self._lineage_id: int = lineage_id
        self._code: str = f"{self._object_type}-{self._lineage_id}"
        self._object_in: EditAcknowledgedRelation = object_in
        self._timepoint: datetime = datetime.utcnow()

    def handle(self) -> ResponseOK:
        relation: Optional[AcknowledgedRelationsTable] = self._repository.get_by_codes(
            self._code,
            self._object_in.Code,
        )
        if not relation:
            raise HTTPException(400, "Acknowledged relation not found")

        # We just edit a side and then push it back in to the table
        side: AcknowledgedRelationSide = relation.get_side(self._code)

        if self._object_in.Explanation is not None:
            side.Explanation = self._object_in.Explanation
        if self._object_in.Acknowledged == False:
            side.disapprove()
        if self._object_in.Acknowledged == True:
            side.approve(self._user.UUID)

        relation.apply_side(side)
        relation.Modified_Date = self._timepoint
        relation.Modified_By_UUID = self._user.UUID

        if self._object_in.Denied == True:
            relation.deny()

        if self._object_in.Deleted == True:
            relation.delete()

        self._db.add(relation)
        self._db.flush()
        self._db.commit()

        return ResponseOK(message="OK")


class EditAcknowledgedRelationEndpoint(Endpoint):
    def __init__(
        self,
        path: str,
        object_type: str,
    ):
        self._path: str = path
        self._object_type: str = object_type

    def register(self, router: APIRouter) -> APIRouter:
        def fastapi_handler(
            lineage_id: int,
            object_in: EditAcknowledgedRelation,
            user: UsersTable = Depends(depends_current_active_user),
            repository: AcknowledgedRelationsRepository = Depends(depends_acknowledged_relations_repository),
            db: Session = Depends(depends_db),
        ) -> ResponseOK:
            handler: EndpointHandler = EndpointHandler(
                db,
                repository,
                user,
                self._object_type,
                lineage_id,
                object_in,
            )
            return handler.handle()

        router.add_api_route(
            self._path,
            fastapi_handler,
            methods=["POST"],
            response_model=ResponseOK,
            summary=f"Edit an acknowledged relation",
            description=None,
            tags=[self._object_type],
        )

        return router


class EditAcknowledgedRelationEndpointResolver(EndpointResolver):
    def get_id(self) -> str:
        return "edit_acknowledged_relation"

    def generate_endpoint(
        self,
        models_resolver: ModelsResolver,
        endpoint_config: EndpointConfig,
        api: Api,
    ) -> Endpoint:
        resolver_config: dict = endpoint_config.resolver_data
        path: str = endpoint_config.prefix + resolver_config.get("path", "")

        return EditAcknowledgedRelationEndpoint(
            path=path,
            object_type=api.object_type,
        )

from datetime import datetime, timezone
from typing import Annotated, Optional

from dependency_injector.wiring import Provide

from sqlalchemy.orm import Session
from dependency_injector.wiring import inject
from fastapi import Depends, HTTPException, status

from app.api.api_container import ApiContainer
from app.api.dependencies import depends_db_session
from app.api.domains.modules.dependencies import depends_active_module
from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.modules.utils import guard_module_not_locked
from app.api.domains.objects.repositories.object_static_repository import ObjectStaticRepository
from app.api.domains.users.dependencies import depends_current_user
from app.api.domains.werkingsgebieden.dependencies import depends_input_geo_werkingsgebied
from app.api.domains.werkingsgebieden.services.input_geo.patch_input_geo_service import PatchInputGeoService, PatchInputGeoServiceFactory
from app.api.domains.werkingsgebieden.types import InputGeoWerkingsgebiedDetailed
from app.api.endpoint import BaseEndpointContext
from app.api.permissions import Permissions
from app.api.services.permission_service import PermissionService
from app.core.tables.modules import ModuleObjectsTable, ModuleTable
from app.core.tables.objects import ObjectStaticsTable
from app.core.tables.users import UsersTable
from app.core.tables.werkingsgebieden import InputGeoWerkingsgebiedenTable


class ModulePatchObjectContext(BaseEndpointContext):
    object_type: str
    target_field: str


@inject
def patch_input_geo_use_werkingsgebied(
    lineage_id: int,
    module: Annotated[ModuleTable, Depends(depends_active_module)],
    context: Annotated[ModulePatchObjectContext, Depends()],
    user: Annotated[UsersTable, Depends(depends_current_user)],
    session: Annotated[Session, Depends(depends_db_session)],
    object_static_repository: Annotated[
        ObjectStaticRepository, Depends(Provide[ApiContainer.object_static_repository])
    ],
    module_object_repository: Annotated[
        ModuleObjectRepository, Depends(Provide[ApiContainer.module_object_repository])
    ],
    permission_service: Annotated[PermissionService, Depends(Provide[ApiContainer.permission_service])],
    patch_input_geo_service_factory: Annotated[PatchInputGeoServiceFactory, Depends(Provide[ApiContainer.patch_input_geo_service_factory])],
    input_geo_werkingsgebied: Annotated[InputGeoWerkingsgebiedenTable, Depends(depends_input_geo_werkingsgebied)],
):
    object_static: Optional[ObjectStaticsTable] = object_static_repository.get_by_object_type_and_id(
        session,
        context.object_type,
        lineage_id,
    )
    if not object_static:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Object static niet gevonden")

    permission_service.guard_valid_user(
        Permissions.module_can_patch_object_in_module,
        user,
        [object_static.Owner_1_UUID, object_static.Owner_2_UUID],
    )
    guard_module_not_locked(module)

    timepoint: datetime = datetime.now(timezone.utc)
    old_record: Optional[ModuleObjectsTable] = module_object_repository.get_latest_by_id(
        session,
        module.Module_ID,
        context.object_type,
        lineage_id,
    )
    if not old_record:
        raise ValueError("lineage_id does not exist in this module")

    patch_service: PatchInputGeoService = patch_input_geo_service_factory.create_service(
        session,
        module,
        input_geo_werkingsgebied,
    )
    result = patch_service.patch(old_record)
    
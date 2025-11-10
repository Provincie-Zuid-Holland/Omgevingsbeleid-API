from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Set, Tuple
import uuid
from fastapi import HTTPException, status
from sqlalchemy import String, func, insert, select
from sqlalchemy.orm import Session
from app.api.domains.modules.services.manage_object_context_service import ManageObjectContextService
import app.api.domains.modules.services.manage_object_context_service as mocs
from app.api.domains.werkingsgebieden.repositories.area_geometry_repository import AreaGeometryRepository
from app.api.domains.werkingsgebieden.repositories.area_repository import AreaRepository
from app.core.tables.others import AreasTable
from app.core.tables.users import UsersTable
from slugify import slugify

from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.objects.repositories.object_static_repository import ObjectStaticRepository
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable
from app.core.tables.objects import ObjectStaticsTable
from app.core.tables.werkingsgebieden import InputGeoOnderverdelingTable, InputGeoWerkingsgebiedenTable


class ObjectResultType(str, Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    IGNORED = "IGNORED"


class PatchGebiedengroepInputGeoService:
    def __init__(
        self,
        object_static_repository: ObjectStaticRepository,
        module_object_repository: ModuleObjectRepository,
        object_context_service: ManageObjectContextService,
        area_repository: AreaRepository,
        area_geometry_repository: AreaGeometryRepository,
        session: Session,
        user: UsersTable,
        onderverdeling_object_type: str,
        input_geo_werkingsgebied: InputGeoWerkingsgebiedenTable,
    ):
        self._object_static_repository: ObjectStaticRepository = object_static_repository
        self._module_object_repository: ModuleObjectRepository = module_object_repository
        self._object_context_service: ManageObjectContextService = object_context_service
        self._area_repository: AreaRepository = area_repository
        self._area_geometry_repository: AreaGeometryRepository = area_geometry_repository
        self._session: Session = session
        self._user: UsersTable = user
        self._onderverdeling_object_type: str = onderverdeling_object_type
        self._input_geo_werkingsgebied: InputGeoWerkingsgebiedenTable = input_geo_werkingsgebied
        self._timepoint: datetime = datetime.now(timezone.utc)

    def patch(self, main_obj: ModuleObjectsTable) -> ModuleObjectsTable:
        used_sub_codes: Set[str] = set()
        something_changed: bool = False

        for onderverdeling in self._input_geo_werkingsgebied.Onderverdelingen:
            sub_object_static: ObjectStaticsTable = self._ensure_static_object(
                main_obj,
                onderverdeling,
            )
            area_uuid: uuid.UUID = self._ensure_area(onderverdeling)
            _sub_object_context: ModuleObjectContextTable = self._ensure_object_context(
                sub_object_static,
                main_obj.Module_ID,
            )

            object_result_action, _sub_object = self._ensure_object_newest_area(
                sub_object_static,
                main_obj.Module_ID,
                area_uuid,
                onderverdeling.Title,
            )
            if object_result_action in [ObjectResultType.CREATED, ObjectResultType.UPDATED]:
                something_changed = True

            used_sub_codes.add(sub_object_static.Code)

        # Patch the main object and set the "gebieden"
        if something_changed:
            new_main_obj: ModuleObjectsTable = self._module_object_repository.patch_module_object(
                self._session,
                main_obj,
                {
                    "Gebieden": list(used_sub_codes),
                },
                self._timepoint,
                self._user.UUID,
            )
            self._session.add(new_main_obj)
            self._session.flush()
            self._session.commit()

            return new_main_obj

        return main_obj

    def _ensure_static_object(
        self,
        main_obj: ModuleObjectsTable,
        onderverdeling: InputGeoOnderverdelingTable,
    ) -> ObjectStaticsTable:
        source_key: str = slugify(f"igo:{onderverdeling.Title}")
        sub_obj_static: Optional[ObjectStaticsTable] = self._object_static_repository.get_by_source(
            self._session,
            source_key,
        )
        if sub_obj_static:
            return sub_obj_static

        return self._create_object_static(main_obj, onderverdeling, source_key)

    def _create_object_static(
        self,
        main_obj: ModuleObjectsTable,
        onderverdeling: InputGeoOnderverdelingTable,
        source_key: str,
    ) -> ObjectStaticsTable:
        generate_id_subq = (
            select(func.coalesce(func.max(ObjectStaticsTable.Object_ID), 0) + 1)
            .select_from(ObjectStaticsTable)
            .filter(ObjectStaticsTable.Object_Type == self._onderverdeling_object_type)
            .scalar_subquery()
        )

        stmt = (
            insert(ObjectStaticsTable)
            .values(
                Object_Type=self._onderverdeling_object_type,
                Object_ID=generate_id_subq,
                Code=(self._onderverdeling_object_type + "-" + func.cast(generate_id_subq, String)),
                Cached_Title=onderverdeling.Title,
                Source_Identifier=source_key,
                # These are inherited from the parent object
                Owner_1_UUID=main_obj.ObjectStatics.Owner_1_UUID,
                Owner_2_UUID=main_obj.ObjectStatics.Owner_2_UUID,
                Client_1_UUID=main_obj.ObjectStatics.Client_1_UUID,
            )
            .returning(ObjectStaticsTable)
        )

        response: Optional[ObjectStaticsTable] = self._session.execute(stmt).scalars().first()
        if response is None:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create new object static")

        return response

    def _ensure_area(self, onderverdeling: InputGeoOnderverdelingTable) -> uuid.UUID:
        if not onderverdeling.Geometry_Hash:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Onderverdeling does not have an Hash")

        existing_area: Optional[AreasTable] = self._area_repository.get_by_source_hash(
            self._session,
            onderverdeling.Geometry_Hash,
        )
        if existing_area:
            return existing_area.UUID

        area_uuid: uuid.UUID = uuid.uuid4()
        self._area_geometry_repository.create_area(
            self._session,
            area_uuid,
            self._timepoint,
            self._user.UUID,
            onderverdeling,
        )
        return area_uuid

    def _ensure_object_context(self, sub_object_static: ObjectStaticsTable, module_id: int) -> ModuleObjectContextTable:
        request = mocs.ExistRequest(
            module_id=module_id,
            object_type=sub_object_static.Object_Type,
            object_id=sub_object_static.Object_ID,
            timepoint=self._timepoint,
            original_adjust_on=None,
            explanation="",
            conclusion="",
            user_uuid=self._user.UUID,
        )
        result: mocs.Result = self._object_context_service.ensure_exists(
            self._session,
            request,
        )
        return result.object_context

    def _ensure_object_newest_area(
        self,
        sub_object_static: ObjectStaticsTable,
        module_id: int,
        area_uuid: uuid.UUID,
        title: str,
    ) -> Tuple[ObjectResultType, ModuleObjectsTable]:
        existing_object: Optional[ModuleObjectsTable] = (
            self._module_object_repository.get_latest_by_module_id_object_code(
                self._session,
                module_id,
                sub_object_static.Code,
            )
        )
        if existing_object is None:
            return ObjectResultType.CREATED, self._create_sub_object(sub_object_static, module_id, area_uuid, title)

        if existing_object.Area_UUID != area_uuid:
            return ObjectResultType.UPDATED, self._modify_sub_object(existing_object, area_uuid, title)

        return ObjectResultType.IGNORED, existing_object

    def _create_sub_object(
        self,
        sub_object_static: ObjectStaticsTable,
        module_id: int,
        area_uuid: uuid.UUID,
        title: str,
    ) -> ModuleObjectsTable:
        module_object = ModuleObjectsTable()

        module_object.Module_ID = module_id
        module_object.Object_Type = sub_object_static.Object_Type
        module_object.Object_ID = sub_object_static.Object_ID
        module_object.Code = sub_object_static.Code
        module_object.Area_UUID = area_uuid
        module_object.Title = title
        module_object.Adjust_On = None
        module_object.UUID = uuid.uuid4()
        module_object.Created_Date = self._timepoint
        module_object.Created_By_UUID = self._user.UUID
        module_object.Modified_Date = self._timepoint
        module_object.Modified_By_UUID = self._user.UUID

        self._session.add(module_object)
        return module_object

    def _modify_sub_object(
        self, existing_object: ModuleObjectsTable, area_uuid: uuid.UUID, title: str
    ) -> ModuleObjectsTable:
        patched_sub_object: ModuleObjectsTable = self._module_object_repository.patch_module_object(
            self._session,
            existing_object,
            {
                "Area_UUID": area_uuid,
                "Title": title,
            },
            self._timepoint,
            self._user.UUID,
        )
        self._session.add(patched_sub_object)
        return patched_sub_object


class PatchGebiedengroepInputGeoServiceFactory:
    def __init__(
        self,
        object_static_repository: ObjectStaticRepository,
        module_object_repository: ModuleObjectRepository,
        object_context_service: ManageObjectContextService,
        area_repository: AreaRepository,
        area_geometry_repository: AreaGeometryRepository,
    ):
        self._object_static_repository: ObjectStaticRepository = object_static_repository
        self._module_object_repository: ModuleObjectRepository = module_object_repository
        self._object_context_service: ManageObjectContextService = object_context_service
        self._area_repository: AreaRepository = area_repository
        self._area_geometry_repository: AreaGeometryRepository = area_geometry_repository

    def create_service(
        self,
        session: Session,
        user: UsersTable,
        onderverdeling_object_type: str,
        input_geo_werkingsgebied: InputGeoWerkingsgebiedenTable,
    ) -> PatchGebiedengroepInputGeoService:
        return PatchGebiedengroepInputGeoService(
            self._object_static_repository,
            self._module_object_repository,
            self._object_context_service,
            self._area_repository,
            self._area_geometry_repository,
            session,
            user,
            onderverdeling_object_type,
            input_geo_werkingsgebied,
        )

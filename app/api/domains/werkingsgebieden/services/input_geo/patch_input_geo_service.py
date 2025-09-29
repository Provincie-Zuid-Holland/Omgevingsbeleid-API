from datetime import datetime, timezone
from typing import Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import String, func, insert, select
from sqlalchemy.orm import Session
from app.api.domains.werkingsgebieden.repositories.area_geometry_repository import AreaGeometryRepository
from app.api.domains.werkingsgebieden.repositories.area_repository import AreaRepository
from app.core.tables.others import AreasTable
from app.core.tables.users import UsersTable
from slugify import slugify

from app.api.domains.modules.repositories.module_object_repository import ModuleObjectRepository
from app.api.domains.objects.repositories.object_static_repository import ObjectStaticRepository
from app.core.tables.modules import ModuleObjectsTable
from app.core.tables.objects import ObjectStaticsTable
from app.core.tables.werkingsgebieden import InputGeoOnderverdelingTable, InputGeoWerkingsgebiedenTable


class PatchInputGeoService:
    def __init__(
        self,
        object_static_repository: ObjectStaticRepository,
        module_object_repository: ModuleObjectRepository,
        area_repository: AreaRepository,
        area_geometry_repository: AreaGeometryRepository,
        session: Session,
        user: UsersTable,
        onderverdeling_object_type: str,
        input_geo_werkingsgebied: InputGeoWerkingsgebiedenTable,
    ):
        self._object_static_repository: ObjectStaticRepository = object_static_repository
        self._module_object_repository: ModuleObjectRepository = module_object_repository
        self._area_repository: AreaRepository = area_repository
        self._area_geometry_repository: AreaGeometryRepository = area_geometry_repository
        self._session: Session = session
        self._user: UsersTable = user
        self._onderverdeling_object_type: str = onderverdeling_object_type
        self._input_geo_werkingsgebied: InputGeoWerkingsgebiedenTable = input_geo_werkingsgebied
        self._timepoint: datetime = datetime.now(timezone.utc)

    def patch(self, main_obj: ModuleObjectsTable):
        for onderverdeling in self._input_geo_werkingsgebied.Onderverdelingen:
            obj_static: ObjectStaticsTable = self._ensure_static_object(
                main_obj,
                onderverdeling,
            )
            area_uuid: uuid.UUID = self._ensure_area(onderverdeling)
            # @todo: continue here


    def _ensure_static_object(self, main_obj: ModuleObjectsTable, onderverdeling: InputGeoOnderverdelingTable) -> ObjectStaticsTable:
        source_key: str = slugify(f"ig:{onderverdeling.Title}")
        sub_obj_static: Optional[ObjectStaticsTable] = self._object_static_repository.get_by_source(self._session, source_key)
        if sub_obj_static:
            return  sub_obj_static
        
        return self._create_object_static(main_obj, onderverdeling, source_key)

    def _create_object_static(self, main_obj: ModuleObjectsTable, onderverdeling: InputGeoOnderverdelingTable, source_key: str) -> ObjectStaticsTable:
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
                # These are inherited from the parent object
                Owner_1_UUID=main_obj.Owner_1_UUID,
                Owner_2_UUID=main_obj.Owner_2_UUID,
                Client_1_UUID=main_obj.Client_1_UUID,
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


class PatchInputGeoServiceFactory:
    def __init__(
        self,
        object_static_repository: ObjectStaticRepository,
        module_object_repository: ModuleObjectRepository,
        area_repository: AreaRepository,
        area_geometry_repository: AreaGeometryRepository,
    ):
        self._object_static_repository: ObjectStaticRepository = object_static_repository
        self._module_object_repository: ModuleObjectRepository = module_object_repository
        self._area_repository: AreaRepository = area_repository
        self._area_geometry_repository: AreaGeometryRepository = area_geometry_repository

    def create_service(
        self,
        session: Session,
        user: UsersTable,
        onderverdeling_object_type: str,
        input_geo_werkingsgebied: InputGeoWerkingsgebiedenTable,

    ) -> PatchInputGeoService:
        return PatchInputGeoService(
            self._object_static_repository,
            self._module_object_repository,
            self._area_repository,
            self._area_geometry_repository,
            session,
            user,
            onderverdeling_object_type,
            input_geo_werkingsgebied,
        )

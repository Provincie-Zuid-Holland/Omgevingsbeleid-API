from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Set

from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_, or_

from app.api.domains.modules.types import ModuleObjectActionFull
from app.core.tables.modules import ModuleObjectContextTable, ModuleObjectsTable, ModuleTable
from app.core.tables.objects import ObjectsTable
from app.core.types import (
    WerkingsgebiedRelatedModuleObjectShort,
    WerkingsgebiedRelatedObjects,
    WerkingsgebiedRelatedObjectShort,
)


class AddWerkingsgebiedRelatedObjectsConfig(BaseModel):
    to_field: str
    werkingsgebied_codes: List[str]


class AddWerkingsgebiedRelatedObjectsService:
    def __init__(
        self,
        session: Session,
        config: AddWerkingsgebiedRelatedObjectsConfig,
        rows: List[BaseModel],
    ):
        self._session: Session = session
        self._config: AddWerkingsgebiedRelatedObjectsConfig = config
        self._rows: List[BaseModel] = rows

    def add_related_objects(self) -> List[BaseModel]:
        related_objects_map: Dict[str, WerkingsgebiedRelatedObjects] = self._fetch()

        for row in self._rows:
            werkingsgebied_code: str = getattr(row, "Code")
            if werkingsgebied_code in related_objects_map:
                setattr(row, self._config.to_field, related_objects_map[werkingsgebied_code])

        return self._rows

    def _fetch(self) -> Dict[str, WerkingsgebiedRelatedObjects]:
        valid_objects: Dict[str, List[WerkingsgebiedRelatedObjectShort]] = self._fetch_valid_objects()
        module_objects: Dict[str, List[WerkingsgebiedRelatedModuleObjectShort]] = self._fetch_module_objects()

        result: Dict[str, WerkingsgebiedRelatedObjects] = {}
        found_werkingsgebieden_codes: Set[str] = set(list(valid_objects.keys()) + list(module_objects.keys()))
        for werkingsgebied_code in found_werkingsgebieden_codes:
            found_valid_objects: List[WerkingsgebiedRelatedObjectShort] = valid_objects.get(werkingsgebied_code, [])
            found_module_objects: List[WerkingsgebiedRelatedModuleObjectShort] = module_objects.get(
                werkingsgebied_code, []
            )

            result[werkingsgebied_code] = WerkingsgebiedRelatedObjects(
                Valid_Objects=found_valid_objects,
                Module_Objects=found_module_objects,
            )

        return result

    def _fetch_valid_objects(self) -> Dict[str, List[WerkingsgebiedRelatedObjectShort]]:
        row_number = (
            func.row_number()
            .over(
                partition_by=ObjectsTable.Code,
                order_by=desc(ObjectsTable.Modified_Date),
            )
            .label("_RowNumber")
        )

        subq = (
            select(
                row_number,
                ObjectsTable.UUID.label("UUID"),
                ObjectsTable.Object_ID.label("Object_ID"),
                ObjectsTable.Object_Type.label("Object_Type"),
                ObjectsTable.Title.label("Title"),
                ObjectsTable.Code,
                ObjectsTable.Werkingsgebied_Code.label("Werkingsgebied_Code"),
                ObjectsTable.Modified_Date,
                ObjectsTable.Start_Validity,
                ObjectsTable.End_Validity,
            )
            .filter(ObjectsTable.Start_Validity <= datetime.now(timezone.utc))
            .subquery()
        )

        stmt = (
            select(subq)
            .filter(subq.c._RowNumber == 1)
            .filter(subq.c.Werkingsgebied_Code.in_(self._config.werkingsgebied_codes))
            .filter(
                or_(
                    subq.c.End_Validity > datetime.now(timezone.utc),
                    subq.c.End_Validity.is_(None),
                )
            )
        )

        db_result = self._session.execute(stmt).mappings().all()
        valid_objects_map: Dict[str, List[WerkingsgebiedRelatedObjectShort]] = defaultdict(list)
        for db_row in db_result:
            valid_object: WerkingsgebiedRelatedObjectShort = WerkingsgebiedRelatedObjectShort.model_validate(db_row)
            valid_objects_map[valid_object.Werkingsgebied_Code].append(valid_object)

        return valid_objects_map

    def _fetch_module_objects(self) -> Dict[str, List[WerkingsgebiedRelatedModuleObjectShort]]:
        subq = (
            select(
                ModuleObjectsTable.UUID.label("UUID"),
                ModuleObjectsTable.Object_ID.label("Object_ID"),
                ModuleObjectsTable.Object_Type.label("Object_Type"),
                ModuleObjectsTable.Title.label("Title"),
                ModuleObjectsTable.Code,
                ModuleObjectsTable.Werkingsgebied_Code.label("Werkingsgebied_Code"),
                ModuleObjectsTable.Modified_Date,
                ModuleTable.Module_ID.label("Module_ID"),
                ModuleTable.Title.label("Module_Title"),
                ModuleObjectContextTable.Action.label("context_action"),
                func.row_number()
                .over(
                    partition_by=(ModuleObjectsTable.Module_ID, ModuleObjectsTable.Code),
                    order_by=desc(ModuleObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleTable, ModuleObjectsTable.Module_ID == ModuleTable.Module_ID)
            .join(
                ModuleObjectContextTable,
                and_(
                    ModuleObjectsTable.Module_ID == ModuleObjectContextTable.Module_ID,
                    ModuleObjectsTable.Code == ModuleObjectContextTable.Code,
                ),
            )
            .where(ModuleTable.Activated == 1)
            .where(ModuleTable.Closed == 0)
            .where(ModuleObjectContextTable.Action != ModuleObjectActionFull.Terminate)
            .where(ModuleObjectContextTable.Hidden == False)
        ).subquery("LatestModuleObjects")

        stmt = (
            select(
                subq.c.UUID,
                subq.c.Object_ID,
                subq.c.Object_Type,
                subq.c.Title,
                subq.c.Werkingsgebied_Code,
                subq.c.Module_ID,
                subq.c.Module_Title,
            )
            .where(subq.c._RowNumber == 1)
            .where(subq.c.Werkingsgebied_Code.in_(self._config.werkingsgebied_codes))
            .order_by(desc(subq.c.Modified_Date))
        )

        db_result = self._session.execute(stmt).mappings().all()
        module_objects_map: Dict[str, List[WerkingsgebiedRelatedModuleObjectShort]] = defaultdict(list)
        for db_row in db_result:
            module_object: WerkingsgebiedRelatedModuleObjectShort = (
                WerkingsgebiedRelatedModuleObjectShort.model_validate(db_row)
            )
            module_objects_map[module_object.Werkingsgebied_Code].append(module_object)

        return module_objects_map


class AddWerkingsgebiedRelatedObjectsServiceFactory:
    def create_service(
        self,
        session: Session,
        config: AddWerkingsgebiedRelatedObjectsConfig,
        rows: List[BaseModel],
    ) -> AddWerkingsgebiedRelatedObjectsService:
        return AddWerkingsgebiedRelatedObjectsService(
            session=session,
            config=config,
            rows=rows,
        )

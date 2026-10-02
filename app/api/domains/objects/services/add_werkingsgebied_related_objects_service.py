from collections import defaultdict
from datetime import UTC, datetime

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
    werkingsgebied_codes: list[str]


class AddWerkingsgebiedRelatedObjectsService:
    def __init__(
        self,
        session: Session,
        config: AddWerkingsgebiedRelatedObjectsConfig,
        rows: list[BaseModel],
    ):
        self._session: Session = session
        self._config: AddWerkingsgebiedRelatedObjectsConfig = config
        self._rows: list[BaseModel] = rows

    def add_related_objects(self) -> list[BaseModel]:
        related_objects_map: dict[str, WerkingsgebiedRelatedObjects] = self._fetch()

        for row in self._rows:
            werkingsgebied_code: str = row.code
            if werkingsgebied_code in related_objects_map:
                setattr(row, self._config.to_field, related_objects_map[werkingsgebied_code])

        return self._rows

    def _fetch(self) -> dict[str, WerkingsgebiedRelatedObjects]:
        valid_objects: dict[str, list[WerkingsgebiedRelatedObjectShort]] = self._fetch_valid_objects()
        module_objects: dict[str, list[WerkingsgebiedRelatedModuleObjectShort]] = self._fetch_module_objects()

        result: dict[str, WerkingsgebiedRelatedObjects] = {}
        found_werkingsgebieden_codes: set[str] = set(list(valid_objects.keys()) + list(module_objects.keys()))
        for werkingsgebied_code in found_werkingsgebieden_codes:
            found_valid_objects: list[WerkingsgebiedRelatedObjectShort] = valid_objects.get(werkingsgebied_code, [])
            found_module_objects: list[WerkingsgebiedRelatedModuleObjectShort] = module_objects.get(
                werkingsgebied_code, []
            )

            result[werkingsgebied_code] = WerkingsgebiedRelatedObjects(
                valid_objects=found_valid_objects,
                module_objects=found_module_objects,
            )

        return result

    def _fetch_valid_objects(self) -> dict[str, list[WerkingsgebiedRelatedObjectShort]]:
        row_number = (
            func.row_number()
            .over(
                partition_by=ObjectsTable.code,
                order_by=desc(ObjectsTable.modified_date),
            )
            .label("_row_number")
        )

        subq = (
            select(
                row_number,
                ObjectsTable.id.label("UUID"),
                ObjectsTable.object_id.label("object_id"),
                ObjectsTable.object_type.label("object_type"),
                ObjectsTable.Title.label("Title"),
                ObjectsTable.code,
                ObjectsTable.Werkingsgebied_Code.label("Werkingsgebied_Code"),
                ObjectsTable.modified_date,
                ObjectsTable.start_validity,
                ObjectsTable.end_validity,
            )
            .filter(ObjectsTable.start_validity <= datetime.now(UTC))
            .subquery()
        )

        stmt = (
            select(subq)
            .filter(subq.c._row_number == 1)
            .filter(subq.c.werkingsgebied_code.in_(self._config.werkingsgebied_codes))
            .filter(
                or_(
                    subq.c.end_validity > datetime.now(UTC),
                    subq.c.end_validity.is_(None),
                )
            )
        )

        db_result = self._session.execute(stmt).mappings().all()
        valid_objects_map: dict[str, list[WerkingsgebiedRelatedObjectShort]] = defaultdict(list)
        for db_row in db_result:
            valid_object: WerkingsgebiedRelatedObjectShort = WerkingsgebiedRelatedObjectShort.model_validate(db_row)
            valid_objects_map[valid_object.werkingsgebied_code].append(valid_object)

        return valid_objects_map

    def _fetch_module_objects(self) -> dict[str, list[WerkingsgebiedRelatedModuleObjectShort]]:
        subq = (
            select(
                ModuleObjectsTable.id.label("UUID"),
                ModuleObjectsTable.object_id.label("object_id"),
                ModuleObjectsTable.object_type.label("object_type"),
                ModuleObjectsTable.Title.label("Title"),
                ModuleObjectsTable.code,
                ModuleObjectsTable.Werkingsgebied_Code.label("Werkingsgebied_Code"),
                ModuleObjectsTable.modified_date,
                ModuleTable.module_id.label("module_id"),
                ModuleTable.title.label("Module_Title"),
                ModuleObjectContextTable.action.label("context_action"),
                func.row_number()
                .over(
                    partition_by=(ModuleObjectsTable.module_id, ModuleObjectsTable.code),
                    order_by=desc(ModuleObjectsTable.modified_date),
                )
                .label("_row_number"),
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleTable, ModuleObjectsTable.module_id == ModuleTable.module_id)
            .join(
                ModuleObjectContextTable,
                and_(
                    ModuleObjectsTable.module_id == ModuleObjectContextTable.module_id,
                    ModuleObjectsTable.code == ModuleObjectContextTable.code,
                ),
            )
            .where(ModuleTable.activated == 1)
            .where(ModuleTable.closed == 0)
            .where(ModuleObjectContextTable.action != ModuleObjectActionFull.Terminate)
            .where(ModuleObjectContextTable.hidden == False)
        ).subquery("LatestModuleObjects")

        stmt = (
            select(
                subq.c.id,
                subq.c.object_id,
                subq.c.object_type,
                subq.c.title,
                subq.c.werkingsgebied_code,
                subq.c.module_id,
                subq.c.module_title,
            )
            .where(subq.c._row_number == 1)
            .where(subq.c.werkingsgebied_code.in_(self._config.werkingsgebied_codes))
            .order_by(desc(subq.c.modified_date))
        )

        db_result = self._session.execute(stmt).mappings().all()
        module_objects_map: dict[str, list[WerkingsgebiedRelatedModuleObjectShort]] = defaultdict(list)
        for db_row in db_result:
            module_object: WerkingsgebiedRelatedModuleObjectShort = (
                WerkingsgebiedRelatedModuleObjectShort.model_validate(db_row)
            )
            module_objects_map[module_object.werkingsgebied_code].append(module_object)

        return module_objects_map


class AddWerkingsgebiedRelatedObjectsServiceFactory:
    def create_service(
        self,
        session: Session,
        config: AddWerkingsgebiedRelatedObjectsConfig,
        rows: list[BaseModel],
    ) -> AddWerkingsgebiedRelatedObjectsService:
        return AddWerkingsgebiedRelatedObjectsService(
            session=session,
            config=config,
            rows=rows,
        )

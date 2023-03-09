from typing import Optional, List
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session
from app.dynamic.db import ObjectStaticsTable

from app.extensions.modules.db.module_objects_table import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleObjectContextTable, ModuleTable
from app.extensions.modules.models.models import ModuleObjectContext


class ModuleRepository:
    def __init__(self, db: Session):
        self._db: Session = db

    def get_by_id(self, id: int) -> Optional[ModuleTable]:
        stmt = select(ModuleTable).where(ModuleTable.Module_ID == id)
        maybe_module = self._db.scalars(stmt).first()

        return maybe_module

    def get_with_filters(
        self, only_active: bool, mine: Optional[UUID]
    ) -> List[ModuleTable]:
        filters = []
        if only_active:
            filters.append(and_(ModuleTable.Closed == False))

        if mine is not None:
            filters.append(
                and_(
                    or_(
                        ModuleTable.Module_Manager_1_UUID == mine,
                        ModuleTable.Module_Manager_2_UUID == mine,
                        ObjectStaticsTable.Owner_1_UUID == mine,
                        ObjectStaticsTable.Owner_2_UUID == mine,
                    )
                )
            )

        stmt = (
            select(ModuleTable)
            .distinct()
            .select_from(ModuleTable)
            .outerjoin(ModuleObjectsTable)
            .outerjoin(ObjectStaticsTable)
            .filter(*filters)
        )

        rows: List[ModuleTable] = [r for r, in self._db.execute(stmt).all()]
        return rows

    def get_modules_containing_object(
           self, 
           only_active: bool, 
           object_type: str,
           object_lineage_id: int,
           mine: Optional[UUID],
       ) -> List[ModuleTable]:
           """
           Retrieve only modules containing the given object_type and lineage_id
           """
           filters = []
           if only_active:
               filters.append(and_(ModuleTable.Closed == False))

           if mine is not None:
               filters.append(
                   and_(
                       or_(
                           ModuleTable.Module_Manager_1_UUID == mine,
                           ModuleTable.Module_Manager_2_UUID == mine,
                           ObjectStaticsTable.Owner_1_UUID == mine,
                           ObjectStaticsTable.Owner_2_UUID == mine,
                       )
                   )
               )

           stmt = (
               select(ModuleTable)
               .distinct()
               .select_from(ModuleTable)
               .join(ModuleObjectContextTable)
               .filter(
                   and_(
                       ModuleObjectContextTable.Object_Type == object_type,
                       ModuleObjectContextTable.Object_ID == object_lineage_id
                   )
               )
           )

           if filters:
               stmt = stmt.filter(*filters)

           rows: List[ModuleTable] = [r for r, in self._db.execute(stmt).all()]
           return rows

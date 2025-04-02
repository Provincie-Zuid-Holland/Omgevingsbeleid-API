from datetime import datetime
from typing import List

from sqlalchemy import case, desc, select
from sqlalchemy.orm import aliased, selectinload
from sqlalchemy.sql import func, literal, or_, union_all

from app.dynamic.db import ObjectsTable
from app.dynamic.repository.repository import BaseRepository
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleObjectContextTable


class PublicationObjectRepository(BaseRepository):
    def fetch_objects(
        self,
        module_id: int,
        timepoint: datetime,
        object_types: List[str],
        field_map: List[str],
    ) -> List[dict]:
        query = self._get_full_query(module_id, timepoint, object_types, field_map)

        result = self._db.execute(query)
        rows = [row._asdict() for row in result]
        return rows

    def _get_object_query(
        module_id: int,
        timepoint: datetime,
        object_types: List[str],
        field_map: List[str],
    ):
        row_number = (
            func.row_number()
            .over(
                partition_by=ObjectsTable.Code,
                order_by=desc(ObjectsTable.Modified_Date),
            )
            .label("_RowNumber")
        )

        subq = (
            select(ObjectsTable, row_number)
            .options(selectinload(ObjectsTable.ObjectStatics))
            .join(ObjectsTable.ObjectStatics)
            .filter(ObjectsTable.Object_Type.in_(object_types))
            .filter(ObjectsTable.Start_Validity < timepoint)
        )

        subq = subq.subquery()
        aliased_objects = aliased(ObjectsTable, subq)
        stmt = (
            select(
                literal(0).label("Module_ID"),
                literal(0).label("_Terminated"),
                *[getattr(aliased_objects, f) for f in field_map],
            )
            .filter(subq.c._RowNumber == 1)
            .filter(
                or_(
                    subq.c.End_Validity >= timepoint,
                    subq.c.End_Validity == None,
                )
            )
            .order_by(desc(subq.c.Modified_Date))
        )
        return stmt

    def _get_module_object_query(
        self,
        module_id: int,
        timepoint: datetime,
        object_types: List[str],
        field_map: List[str],
    ):
        subq = (
            select(
                ModuleObjectsTable,
                func.row_number()
                .over(
                    partition_by=ModuleObjectsTable.Code,
                    order_by=desc(ModuleObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
                case((ModuleObjectContextTable.Action == "Terminate", 1), else_=0).label("_Terminated"),
            )
            .select_from(ModuleObjectsTable)
            .join(ModuleObjectsTable.ModuleObjectContext)
            .filter(ModuleObjectsTable.Module_ID == module_id)
            .filter(ModuleObjectsTable.Modified_Date < timepoint)
            .filter(ModuleObjectsTable.Object_Type.in_(object_types))
            .filter(ModuleObjectContextTable.Hidden == False)
        ).subquery()

        aliased_objects = aliased(ModuleObjectsTable, subq)
        stmt = (
            select(
                aliased_objects.Module_ID,
                subq.c._Terminated,
                *[getattr(aliased_objects, f) for f in field_map],
            )
            .filter(subq.c._RowNumber == 1)
            .filter(subq.c.Deleted == False)
        )
        return stmt

    def _get_full_query(
        self,
        module_id: int,
        timepoint: datetime,
        object_types: List[str],
        field_map: List[str],
    ):
        object_query = self._get_object_query(timepoint, object_types, field_map)
        module_query = self._get_module_object_query(module_id, timepoint, object_types, field_map)
        union_query = (
            union_all(
                # alias().select() is a cheat to force parentheses
                # Else the union might fail on sqlite
                (object_query.alias().select()),
                (module_query.alias().select()),
            )
        ).alias("combined")

        row_number_query = select(
            union_query.c.Module_ID,
            union_query.c._Terminated,
            *[getattr(union_query.c, f) for f in field_map],
            func.row_number()
            .over(partition_by=union_query.c.Code, order_by=desc(union_query.c.Module_ID))
            .label("rnk"),
        ).alias("ranked_results")

        final_query = (
            select(
                row_number_query.c.Module_ID,
                *[getattr(row_number_query.c, f) for f in field_map],
            )
            .filter(row_number_query.c.rnk == 1)
            .filter(row_number_query.c._Terminated == 0)
        )

        return final_query

from datetime import datetime

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import aliased
from sqlalchemy.orm.session import object_session

from app.dynamic.db.object_static_table import ObjectStaticsTable
from app.dynamic.db.objects_table import ObjectsTable


def get_effective_object(self):
    subq = (
        select(
            ObjectsTable,
            func.row_number()
            .over(
                partition_by=ObjectsTable.Code,
                order_by=desc(ObjectsTable.Modified_Date),
            )
            .label("_RowNumber"),
        )
        .select_from(ObjectsTable)
        .filter(ObjectsTable.Start_Validity <= datetime.utcnow())
        .filter(ObjectsTable.Code == self.Code)
    )

    subq = subq.subquery()
    aliased_objects = aliased(ObjectsTable, subq)
    query = (
        select(aliased_objects)
        .outerjoin(ObjectStaticsTable, subq.c.Code == ObjectStaticsTable.Code)
        .filter(subq.c._RowNumber == 1)
        .filter(
            or_(
                subq.c.End_Validity > datetime.utcnow(),
                subq.c.End_Validity == None,
            )
        )
        .order_by(desc(subq.c.Modified_Date))
    )

    db = object_session(self)
    result = db.scalars(query).first()
    return result


def extend_with_attributes(table):
    setattr(table, "Effective_Object", hybrid_property(get_effective_object))

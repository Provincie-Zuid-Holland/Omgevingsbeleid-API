from sqlalchemy import select, func, desc, String
from sqlalchemy.orm import aliased, mapped_column
from sqlalchemy.orm.session import object_session
from sqlalchemy.ext.hybrid import hybrid_property

from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable


def get_last_module_version(self):
    subq = (
        select(
            ModuleObjectsTable,
            func.row_number()
            .over(
                partition_by=ModuleObjectsTable.Code,
                order_by=desc(ModuleObjectsTable.Modified_Date),
            )
            .label("_RowNumber"),
        )
        .select_from(ModuleObjectsTable)
        .filter(ModuleObjectsTable.Code == self.Code)
    )
    subq = subq.subquery()
    aliased_objects = aliased(ModuleObjectsTable, subq)
    stmt = (
        select(aliased_objects)
        .filter(subq.c._RowNumber == 1)
        .order_by(desc(subq.c.Modified_Date))
    )
    db = object_session(self)
    result = db.scalars(stmt).all()
    return result


def extend_with_attributes(table):
    setattr(table, "Latest_Module_Version", hybrid_property(get_last_module_version))
    setattr(table, "Cached_Title", mapped_column("Cached_Title", String(255), nullable=True))

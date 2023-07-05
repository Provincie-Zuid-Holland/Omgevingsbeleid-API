from sqlalchemy.orm.session import Session
from sqlalchemy.sql import select

from app.dynamic.db.object_static_table import ObjectStaticsTable


def get_unique_object_types(session: Session):
    """
    Fetch list of existing object types in the DB.
    """
    stmt = select(ObjectStaticsTable.Object_Type).distinct()
    result = session.execute(stmt)
    return [row[0] for row in result.fetchall()]

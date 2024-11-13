from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.session import object_session

from app.dynamic.db import ObjectsTable
from app.dynamic.repository.object_repository import ObjectRepository
from app.extensions.lineage_resolvers.models import NextObjectValidities

#
#    Define extra attributes or dynamic sqlalchemy properties for tables outside of this
#    extension, which will be set on this extension init
#    to prevent mixing logic.
#


def get_next_object_validities(self):
    query = ObjectRepository.next_valid_by_uuid_query(object_uuid=self.UUID)
    row = object_session(self).execute(query).first()
    if row is None:
        return None

    next_obj = row[0]
    if next_obj.UUID == self.UUID:
        return None

    next_object_validities = NextObjectValidities(
        Object_UUID=next_obj.UUID,
        Start_Validity=next_obj.Start_Validity,
        End_Validity=next_obj.End_Validity,
        Created_Date=next_obj.Created_Date,
        Modified_Date=next_obj.Modified_Date,
    )
    return next_object_validities

def extend_with_attributes():
    setattr(ObjectsTable, "Next_Version", hybrid_property(get_next_object_validities))

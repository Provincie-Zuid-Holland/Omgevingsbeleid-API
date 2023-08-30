from typing import List
from sqlalchemy import String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.session import object_session

from app.dynamic.db.object_static_table import ObjectStaticsTable
from app.dynamic.db.objects_table import ObjectsTable
from app.extensions.modules.models.models import ModuleStatusCode, PublicModuleObjectRevision
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository

#
#    Define extra attributes or dynamic sqlalchemy properties for tables outside of this
#    extension, which will be set on this extension init
#    to prevent mixing logic.
#


def get_object_public_revisions(self):
    """
    Find any module objects with a minimum status as active draft version of this current Object.
    """
    min_status_list = ModuleStatusCode.after(ModuleStatusCode.Ontwerp_GS)
    query = ModuleObjectRepository.latest_per_module_query(
        code=self.Code, status_filter=min_status_list, is_active=True
    )
    session = object_session(self)
    rows = session.execute(query).all()

    return [
        PublicModuleObjectRevision(
            Module_Object_UUID=module_object.UUID,
            Module_ID=module.Module_ID,
            Module_Title=module.Title,
            Module_Status=module.Current_Status,
        )
        for module_object, module in rows
    ]


def extend_with_attributes():
    setattr(ObjectsTable, "Public_Revisions", hybrid_property(get_object_public_revisions))
    setattr(ObjectStaticsTable, "Cached_Title", mapped_column("Cached_Title", String(255), nullable=True))

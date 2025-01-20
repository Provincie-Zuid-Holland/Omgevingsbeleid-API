from typing import Tuple
from sqlalchemy import Select, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.session import Session, object_session

from app.dynamic.db import ObjectsTable, ObjectStaticsTable
from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleTable
from app.extensions.modules.models.models import ModuleObjectActionFilter, ModuleStatusCode, PublicModuleObjectRevision
from app.extensions.modules.repository.module_object_repository import (
    ModuleObjectRepository,
)

#
#    Define extra attributes or dynamic sqlalchemy properties for tables outside of this
#    extension, which will be set on this extension init
#    to prevent mixing logic.
#


def get_object_public_revisions(self):
    """
    Find any module objects with a minimum status as active draft version of this current Object.
    """
    min_status_list = ModuleStatusCode.values()
    session: Session = object_session(self)
    query: Select[Tuple[ModuleObjectsTable, ModuleTable, ModuleObjectActionFilter]] = (
        ModuleObjectRepository.latest_per_module_query(code=self.Code, status_filter=min_status_list, is_active=True)
    )
    rows = session.execute(query).all()
    public_revisions = []
    for module_object, module, context_action in rows:
        public_revisions.append(
            PublicModuleObjectRevision(
                Module_Object_UUID=module_object.UUID,
                Module_ID=module.Module_ID,
                Module_Title=module.Title,
                Module_Status=module.Current_Status,
                Action=context_action,
            )
        )
    return public_revisions


def extend_with_attributes():
    setattr(ObjectsTable, "Public_Revisions", hybrid_property(get_object_public_revisions))
    setattr(ObjectStaticsTable, "Cached_Title", mapped_column("Cached_Title", String(255), nullable=True))

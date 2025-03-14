from collections import namedtuple
from typing import Tuple

from sqlalchemy import Select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.session import Session, object_session

from app.extensions.modules.db.module_objects_tables import ModuleObjectsTable
from app.extensions.modules.db.tables import ModuleTable
from app.extensions.modules.models.models import ModuleObjectActionFull, ModuleStatusCode, PublicModuleObjectRevision
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository

ModuleObjectDTO = namedtuple(
    "ModuleObjectDTO",
    [
        "Module_Object_UUID",
        "Module_ID",
        "Module_Title",
        "Module_Status",
        "Action",
    ],
)


def get_object_public_revisions(self):
    min_status_list = ModuleStatusCode.values()
    session: Session = object_session(self)
    query: Select[Tuple[ModuleObjectsTable, ModuleTable, ModuleObjectActionFull]] = (
        ModuleObjectRepository.latest_per_module_query(code=self.Code, status_filter=min_status_list, is_active=True)
    )
    rows = session.execute(query).all()
    public_revisions = [
        PublicModuleObjectRevision.model_validate(
            ModuleObjectDTO(
                Module_Object_UUID=module_object.UUID,
                Module_ID=module.Module_ID,
                Module_Title=module.Title,
                Module_Status=module.Current_Status,
                Action=context_action,
            )
        )
        for module_object, module, context_action in rows
    ]
    return public_revisions


def build_object_public_revisions_property():
    return hybrid_property(get_object_public_revisions)

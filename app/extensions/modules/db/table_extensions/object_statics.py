from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Session
from sqlalchemy.orm.session import object_session
from sqlalchemy.ext.hybrid import hybrid_property

from app.extensions.modules.repository import ModuleObjectRepository


def get_last_module_version(self):
    query = ModuleObjectRepository.latest_versions_query(code=self.Code)
    db: Session = object_session(self)
    return db.scalars(query).first()


def extend_with_attributes(table):
    """
    used for declaring dynamic orm properties to a given table on app init
    without placing this logic outside of the extension.
    """
    setattr(table, "Latest_Module_Version", hybrid_property(get_last_module_version))
    setattr(
        table, "Cached_Title", mapped_column("Cached_Title", String(255), nullable=True)
    )

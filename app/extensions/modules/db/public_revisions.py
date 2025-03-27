
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.session import Session, object_session

from app.extensions.modules.models.models import PublicModuleObjectRevision, PublicModuleStatusCode
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository


def get_object_public_revisions(self):
    session: Session = object_session(self)
    query = ModuleObjectRepository.public_revisions_per_module_query(
        code=self.Code, allowed_status_list=PublicModuleStatusCode.values()
    )
    rows = session.execute(query).all()
    public_revisions = [PublicModuleObjectRevision.model_validate(row) for row in rows]
    return public_revisions


def build_object_public_revisions_property():
    return hybrid_property(get_object_public_revisions)

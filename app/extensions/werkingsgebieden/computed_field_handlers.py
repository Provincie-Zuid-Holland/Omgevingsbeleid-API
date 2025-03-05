from typing import List

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dynamic.computed_fields.models import ComputedField
from app.dynamic.config.models import DynamicObjectModel
from app.dynamic.repository.object_repository import ObjectRepository
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository
from app.extensions.modules.repository.object_provider import ObjectProvider
from app.extensions.werkingsgebieden.service.werkingsgebied_related_objects import WerkingsgebiedRelatedObjectService


def process_werkingsgebied_related_objects(
    db: Session, dynamic_objects: List[BaseModel], dynamic_obj_model: DynamicObjectModel, computed_field: ComputedField
):
    object_provider = ObjectProvider(
        object_repository=ObjectRepository(db),
        module_object_repository=ModuleObjectRepository(db),
    )
    service = WerkingsgebiedRelatedObjectService(
        object_provider=object_provider,
        rows=dynamic_objects,
        dynamic_obj_model=dynamic_obj_model,
        computed_field=computed_field,
    )
    return service.fetch_related_objects()

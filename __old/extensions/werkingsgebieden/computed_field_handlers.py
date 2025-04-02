from pydantic.main import BaseModel

from app.dynamic.computed_fields.handler_context import HandlerContext
from app.dynamic.repository.object_repository import ObjectRepository
from app.extensions.modules.repository.module_object_repository import ModuleObjectRepository
from app.extensions.modules.repository.object_provider import ObjectProvider
from app.extensions.werkingsgebieden.service.werkingsgebied_related_objects import WerkingsgebiedRelatedObjectService


def process_werkingsgebied_related_objects(context: HandlerContext) -> BaseModel:
    object_provider = ObjectProvider(
        object_repository=ObjectRepository(context.db),
        module_object_repository=ModuleObjectRepository(context.db),
    )
    service = WerkingsgebiedRelatedObjectService(
        object_provider=object_provider,
        rows=context.dynamic_objects,
        dynamic_obj_model=context.dynamic_obj_model,
        computed_field=context.computed_field,
    )
    return service.fetch_related_objects()

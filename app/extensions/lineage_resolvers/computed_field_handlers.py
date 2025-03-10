from app.dynamic.computed_fields.handler_context import HandlerContext
from app.extensions.lineage_resolvers.service.next_object_validities_service import NextObjectVersionService


def batch_load_next_object_validities(context: HandlerContext):
    service = NextObjectVersionService(
        db=context.db,
        dynamic_objects=context.dynamic_objects,
        dynamic_obj_model=context.dynamic_obj_model,
        computed_field=context.computed_field,
    )
    return service.process_batch()


def load_next_object_validities(context: HandlerContext):
    service = NextObjectVersionService(
        db=context.db,
        dynamic_objects=context.dynamic_objects,
        dynamic_obj_model=context.dynamic_obj_model,
        computed_field=context.computed_field,
    )
    return service.process_single_item()

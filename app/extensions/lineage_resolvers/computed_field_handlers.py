from typing import List

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dynamic.computed_fields.models import ComputedField
from app.dynamic.config.models import DynamicObjectModel
from app.extensions.lineage_resolvers.service.next_object_validities_service import NextObjectVersionService


def batch_load_next_object_validities(
    db: Session, dynamic_objects: List[BaseModel], dynamic_obj_model: DynamicObjectModel, computed_field: ComputedField
):
    service = NextObjectVersionService(
        db=db, dynamic_objects=dynamic_objects, dynamic_obj_model=dynamic_obj_model, computed_field=computed_field
    )
    return service.process_batch()


def load_next_object_validities(
    db: Session, dynamic_objects: List[BaseModel], dynamic_obj_model: DynamicObjectModel, computed_field: ComputedField
):
    service = NextObjectVersionService(
        db=db, dynamic_objects=dynamic_objects, dynamic_obj_model=dynamic_obj_model, computed_field=computed_field
    )
    return service.process_single_item()

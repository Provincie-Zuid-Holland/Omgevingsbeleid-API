from typing import Any, Dict, List, Type, get_args
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Column, Select, func, select
from sqlalchemy.orm import Session, load_only

from app.dynamic.computed_fields.models import ComputedField
from app.dynamic.config.models import DynamicObjectModel
from app.dynamic.db.tables import ObjectsTable


class NextObjectVersionService:
    """
    Handles loading next object versions in batch for dynamic objects
    """

    def __init__(
        self,
        db: Session,
        dynamic_objects: List[BaseModel],
        dynamic_obj_model: DynamicObjectModel,
        computed_field: ComputedField,
    ):
        self._db: Session = db
        self._dynamic_objects: List[BaseModel] = dynamic_objects
        self._dynamic_obj_model: DynamicObjectModel = dynamic_obj_model
        self._computed_field: ComputedField = computed_field

    def process_single_item(self) -> List[BaseModel]:
        if len(self._dynamic_objects) != 1:
            raise ValueError("Trying to process a single obj but multiple rows found")

        row: BaseModel = self._dynamic_objects[0]
        computed_field_model: Type[BaseModel] = self._extract_computed_field_model()
        field_name: str = self._computed_field.attribute_name

        next_obj_query = self._query_next_object_version_by_uuid(
            object_uuid=row.UUID, model_fields=computed_field_model.model_fields
        )
        next_obj = self._db.execute(next_obj_query).scalars().first()

        next_version = computed_field_model.model_validate(next_obj) if next_obj else None
        self._dynamic_objects[0] = row.model_copy(update={field_name: next_version})
        return self._dynamic_objects

    def process_batch(self) -> List[BaseModel]:
        object_uuids = [obj.UUID for obj in self._dynamic_objects]
        if not object_uuids:
            return self._dynamic_objects

        field_name: str = self._computed_field.attribute_name
        computed_field_model: Type[BaseModel] = self._extract_computed_field_model()
        batch_next_versions_query: Select = self._batch_next_version_query(
            object_uuids=object_uuids, model_fields=computed_field_model.model_fields
        )
        rows = self._db.execute(batch_next_versions_query).all()

        # map the original uuids to the next versions
        next_versions: Dict[UUID, dict] = {}
        for row in rows:
            ref_uuid: UUID = row._mapping["ref_uuid"]
            next_versions[ref_uuid] = dict(row._mapping)

        # merge results back and convert ORM objects to Pydantic models in the same loop
        for row in self._dynamic_objects:
            orm_obj = next_versions.get(row.UUID)
            next_version = computed_field_model.model_validate(orm_obj) if orm_obj else None
            setattr(row, field_name, next_version)

        return self._dynamic_objects

    def _query_next_object_version_by_uuid(self, object_uuid: UUID, model_fields: Dict[str, Any]):
        select_cols: List[Column] = self._extract_select_columns(model_fields)
        reference_obj = (
            select(ObjectsTable.Code, ObjectsTable.Modified_Date).filter(ObjectsTable.UUID == object_uuid).subquery()
        )
        stmt = (
            select(ObjectsTable)
            .options(load_only(*select_cols))
            .filter(ObjectsTable.Code == reference_obj.c.Code)
            .filter(ObjectsTable.Modified_Date > reference_obj.c.Modified_Date)
            .order_by(ObjectsTable.Modified_Date.asc())
            .limit(1)
        )
        return stmt

    def _batch_next_version_query(
        self,
        object_uuids: List[UUID],
        model_fields: Dict[str, Any],
    ) -> Select:
        # acts as context to match new versions against
        reference_subq = (
            select(
                ObjectsTable.UUID.label("ref_uuid"),
                ObjectsTable.Code.label("ref_code"),
                ObjectsTable.Modified_Date.label("ref_modified_date"),
            ).where(ObjectsTable.UUID.in_(object_uuids))
        ).subquery("input_object_reference")

        row_number_col = (
            func.row_number()
            .over(partition_by=reference_subq.c.ref_uuid, order_by=ObjectsTable.Modified_Date.asc())
            .label("_RowNumber")
        )

        next_version_cols: List[Column] = self._extract_select_columns(model_fields)
        # the actual query matching the input rows CTE -> next versions
        next_obj_subq = (
            select(reference_subq.c.ref_uuid, row_number_col, *next_version_cols)
            .join(
                ObjectsTable,
                (ObjectsTable.Code == reference_subq.c.ref_code)
                & (ObjectsTable.Modified_Date > reference_subq.c.ref_modified_date),
            )
            .subquery("next_object_versions_view")
        )

        return select(next_obj_subq).where(next_obj_subq.c._RowNumber == 1)

    def _extract_computed_field_model(self) -> Type[BaseModel]:
        """
        gets the computed field schema from the dynamic object response model
        """
        field_name = self._computed_field.attribute_name
        field_info = self._dynamic_obj_model.pydantic_model.model_fields[field_name]
        field_annotation = field_info.annotation
        if field_annotation is None:
            raise ValueError(f"error getting computed field schema for response model field: {field_name}")

        has_type_wrapper = self._computed_field.is_list or self._computed_field.is_optional
        computed_field_model = get_args(field_annotation)[0] if has_type_wrapper else field_annotation

        return computed_field_model

    def _extract_select_columns(self, model_fields: Dict[str, Any]) -> List[Column]:
        next_version_cols: List[Column] = [getattr(ObjectsTable, col_name) for col_name in model_fields.keys()]
        return next_version_cols

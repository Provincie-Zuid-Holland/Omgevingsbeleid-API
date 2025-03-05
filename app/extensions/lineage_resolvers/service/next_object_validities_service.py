from datetime import datetime, timezone
from typing import Dict, List, Optional, Type

from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

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

    def process_single_item(self) -> BaseModel:
        if len(self._dynamic_objects) != 1:
            raise ValueError("Trying to process a single obj but multiple rows found")

        item = self._dynamic_objects[0]
        code = getattr(item, "Code")
        modified_date = getattr(item, "Modified_Date")

        next_obj = self._query_next_object_version(code, modified_date)

        field_name = self._computed_field.attribute_name
        computed_field_model: Type[BaseModel] = self._dynamic_obj_model.pydantic_model.__fields__[field_name].type_

        if next_obj:
            next_version = computed_field_model.from_orm(next_obj)
            setattr(item, field_name, next_version)
        else:
            setattr(item, field_name, None)

        return item

    def process_batch(self) -> List[BaseModel]:
        object_uuids = [row.UUID for row in self._dynamic_objects]

        if not object_uuids:
            return self._dynamic_objects

        uuid_to_code_map = {row.UUID: row.Code for row in self._dynamic_objects}
        uuid_to_modified_date_map = {row.UUID: row.Modified_Date for row in self._dynamic_objects}

        next_versions: Dict[str, ObjectsTable] = self._batch_query_next_versions(
            uuid_to_code_map, uuid_to_modified_date_map
        )

        # extract the computed field model
        field_name = self._computed_field.attribute_name
        computed_field_model: Type[BaseModel] = self._dynamic_obj_model.pydantic_model.__fields__[field_name].type_

        # merge results back and convert ORM objects to Pydantic models in the same loop
        for row in self._dynamic_objects:
            orm_obj = next_versions.get(row.UUID)
            next_version = computed_field_model.from_orm(orm_obj) if orm_obj else None
            setattr(row, field_name, next_version)

        return self._dynamic_objects

    def _query_next_object_version(self, code: str, modified_date: datetime) -> Optional[ObjectsTable]:
        # Valid next object version TODO: move to repo?
        stmt = (
            select(ObjectsTable)
            .options(selectinload(ObjectsTable.ObjectStatics))
            .join(ObjectsTable.ObjectStatics)
            .filter(ObjectsTable.Code == code)
            .filter(ObjectsTable.Modified_Date > modified_date)
            .filter(ObjectsTable.Start_Validity <= datetime.now(timezone.utc))
            .filter(
                or_(
                    ObjectsTable.End_Validity > datetime.now(timezone.utc),
                    ObjectsTable.End_Validity == None,
                )
            )
            .order_by(ObjectsTable.Modified_Date.asc())
            .limit(1)
        )

        return self._db.execute(stmt).scalars().first()

    def _batch_query_next_versions(
        self, uuid_to_code_map: Dict[str, str], uuid_to_modified_date_map: Dict[str, datetime]
    ) -> Dict[str, ObjectsTable]:
        if not uuid_to_code_map:
            return {}

        potential_next_objects = self._query_potential_next_objects(set(uuid_to_code_map.values()))
        return self._process_next_version_candidates(
            potential_next_objects, uuid_to_code_map, uuid_to_modified_date_map
        )

    def _query_potential_next_objects(self, unique_codes: set) -> List[ObjectsTable]:
        stmt = (
            select(ObjectsTable)
            .options(selectinload(ObjectsTable.ObjectStatics))
            .join(ObjectsTable.ObjectStatics)
            .filter(ObjectsTable.Code.in_(unique_codes))
            .filter(ObjectsTable.Start_Validity <= datetime.now(timezone.utc))
            .filter(
                or_(
                    ObjectsTable.End_Validity > datetime.now(timezone.utc),
                    ObjectsTable.End_Validity == None,
                )
            )
        )

        return self._db.execute(stmt).scalars().all()

    def _process_next_version_candidates(
        self,
        candidate_objects: List[ObjectsTable],
        uuid_to_code_map: Dict[str, str],
        uuid_to_modified_date_map: Dict[str, datetime],
    ) -> Dict[str, ObjectsTable]:
        result_map = {}

        # group potential next version objects by code
        objects_by_code = {}
        for obj in candidate_objects:
            if obj.Code not in objects_by_code:
                objects_by_code[obj.Code] = []
            objects_by_code[obj.Code].append(obj)

        # find next version per UUID
        for uuid, code in uuid_to_code_map.items():
            modified_date = uuid_to_modified_date_map[uuid]

            # find same code with later modified date
            candidates = objects_by_code.get(code, [])
            next_obj = None

            for obj in candidates:
                if obj.UUID == uuid or obj.Modified_Date <= modified_date:
                    continue

                if next_obj is None or obj.Modified_Date < next_obj.Modified_Date:
                    next_obj = obj

            if next_obj:
                result_map[uuid] = next_obj

        return result_map

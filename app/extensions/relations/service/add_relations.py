from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from pydantic import BaseModel
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.dynamic.config.models import DynamicObjectModel, Model
from app.dynamic.converter import Converter
from app.dynamic.db.objects_table import ObjectsTable
from app.extensions.relations.db.tables import RelationsTable


@dataclass
class ObjectTypeDetails:
    object_id: str
    to_field: str
    wrapped_with_relation_data: bool


@dataclass
class Config:
    object_codes: List[str]
    object_types: List[str]
    object_type_details: Dict[str, ObjectTypeDetails]


class AddRelationsService:
    def __init__(
        self,
        converter: Converter,
        db: Session,
        rows: List[BaseModel],
        response_model: Model,
    ):
        self._converter: Converter = converter
        self._db: Session = db
        self._rows: List[BaseModel] = rows
        self._response_model: Model = response_model

    def add_relations(self) -> List[BaseModel]:
        config: Optional[Config] = self._collect_config()
        if not config:
            return self._rows

        relation_rows: List[dict] = self._fetch_relation_rows(config)

        """
        relations=
        {
            # target/to (owner)
            'ambitie-1': {
                # object-type of the relation
                # used to map to the right field in the target
                'Beleidsdoelen': [
                    {row},
                    {row},
                ],
                'Beleidskeuzes': [
                    {row},
                    {row},
                ],
            }
        }
        """
        relations = defaultdict(lambda: defaultdict(list))
        for relation_row in relation_rows:
            # Determine the owner
            target_code: str = relation_row.get("_Relation_From_Code")
            if relation_row.get("_Relation_From_Code") == relation_row.get("Code"):
                target_code = relation_row["_Relation_To_Code"]

            relation_object_type: str = relation_row.get("Object_Type")
            object_config: ObjectTypeDetails = config.object_type_details[relation_object_type]

            deserialized_relation_row: dict = self._converter.deserialize(object_config.object_id, relation_row)

            # Created wrapped relation model if configures with wrapped_with_relation_data
            field_value: dict = deserialized_relation_row
            if object_config.wrapped_with_relation_data:
                field_value = {
                    "Relation": {
                        "Object_Type": relation_row.get("Object_Type"),
                        "Object_ID": relation_row.get("Object_ID"),
                        "Description": relation_row.get("_Relation_Description"),
                    },
                    "Object": deserialized_relation_row,
                }

            relations[target_code][object_config.to_field].append(field_value)

        # Now we union the relation "rows" into the event rows
        result_rows: List[dict] = []
        for row in self._rows:
            if getattr(row, "Code") in relations:
                for field_name, content in relations[getattr(row, "Code")].items():
                    setattr(row, field_name, content)
            result_rows.append(row)

        return result_rows

    def _collect_config(self) -> Optional[Config]:
        if not isinstance(self._response_model, DynamicObjectModel):
            return None
        if not "relations" in self._response_model.service_config:
            return None

        object_codes: List[str] = list(set([getattr(r, "Code") for r in self._rows]))

        relations_config: dict = self._response_model.service_config.get("relations")
        objects_config: List[dict] = relations_config.get("objects")

        to_field_map: Dict[str, ObjectTypeDetails] = {}
        object_types: Set[str] = set()
        for object_config in objects_config:
            object_id: str = object_config.get("object_id")
            object_type: str = object_config.get("object_type")
            to_field: str = object_config.get("to_field")
            wrapped_with_relation_data: bool = object_config.get("wrapped_with_relation_data", False)

            object_types.add(object_type)
            to_field_map[object_type] = ObjectTypeDetails(
                object_id,
                to_field,
                wrapped_with_relation_data,
            )

        return Config(
            object_codes,
            list(object_types),
            to_field_map,
        )

    def _fetch_relation_rows(self, config: Config) -> List[dict]:
        subq = (
            select(
                ObjectsTable,
                RelationsTable.From_Code.label("_Relation_From_Code"),
                RelationsTable.To_Code.label("_Relation_To_Code"),
                RelationsTable.Description.label("_Relation_Description"),
                func.row_number()
                .over(
                    partition_by=ObjectsTable.Code,
                    order_by=desc(ObjectsTable.Modified_Date),
                )
                .label("_RowNumber"),
            )
            .select_from(RelationsTable)
            .join(
                ObjectsTable,
                ObjectsTable.Code.in_([RelationsTable.From_Code, RelationsTable.To_Code]),
            )
            .filter(
                or_(
                    RelationsTable.From_Code.in_(config.object_codes),
                    RelationsTable.To_Code.in_(config.object_codes),
                )
            )
            .filter(ObjectsTable.Object_Type.in_(config.object_types))
            .subquery()
        )

        stmt = select(subq).filter(subq.c._RowNumber == 1)

        rows = self._db.execute(stmt).all()
        dict_rows = [r._asdict() for r in rows]
        return dict_rows

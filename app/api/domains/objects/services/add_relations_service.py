from collections import defaultdict
from typing import Any, Dict, List, Optional, Union, get_args

from pydantic import BaseModel
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.core.tables.objects import ObjectsTable
from app.core.tables.others import RelationsTable
from app.core.types import DynamicObjectModel, Model


class ObjectRelationConfig(BaseModel):
    object_type: str
    object_id: str
    to_field: str
    model_id: str
    wrapped_with_relation_data: bool = False


class RelationsConfig(BaseModel):
    objects: List[ObjectRelationConfig]


class Config(BaseModel):
    object_codes: List[str]
    object_types: List[str]
    object_type_details: Dict[str, ObjectRelationConfig]


class AddRelationsService:
    def __init__(
        self,
        session: Session,
        rows: List[BaseModel],
        response_model: Model,
    ):
        self._session: Session = session
        self._rows: List[BaseModel] = rows
        self._response_model: Union[DynamicObjectModel, Model] = response_model

    def add_relations(self) -> List[BaseModel]:
        config: Optional[Config] = self._collect_config()
        if not config:
            return self._rows

        relation_rows: List[Dict[str, Any]] = self._fetch_relation_rows(config)

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
            target_code: str = relation_row["_Relation_From_Code"]
            if relation_row["_Relation_From_Code"] == relation_row["Code"]:
                target_code = relation_row["_Relation_To_Code"]

            relation_object_type: str = relation_row["Object_Type"]
            object_config: ObjectRelationConfig = config.object_type_details[relation_object_type]

            # extract the created relation-object pydantic model
            field_annotation = self._response_model.pydantic_model.model_fields[object_config.to_field].annotation
            relation_row_model = get_args(field_annotation)[0]

            # Created wrapped relation model if configures with wrapped_with_relation_data
            field_value: dict = relation_row
            if object_config.wrapped_with_relation_data:
                field_value = {
                    "Relation": {
                        "Object_Type": relation_row.get("Object_Type"),
                        "Object_ID": relation_row.get("Object_ID"),
                        "Description": relation_row.get("_Relation_Description"),
                    },
                    "Object": relation_row,
                }

            field_result: BaseModel = relation_row_model.model_validate(field_value)
            relations[target_code][object_config.to_field].append(field_result)

        # Now we union the relation "rows" into the event rows
        result_rows: List[BaseModel] = []
        for row in self._rows:
            if getattr(row, "Code") in relations:
                for field_name, content in relations[getattr(row, "Code")].items():
                    setattr(row, field_name, content)
            result_rows.append(row)

        return result_rows

    def _fetch_relation_rows(self, config: Config) -> List[Dict[str, Any]]:
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
                or_(ObjectsTable.Code == RelationsTable.From_Code, ObjectsTable.Code == RelationsTable.To_Code),
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

        rows = self._session.execute(stmt).all()
        dict_rows = [r._asdict() for r in rows]
        return dict_rows

    def _collect_config(self) -> Optional[Config]:
        if not isinstance(self._response_model, DynamicObjectModel):
            return None
        if not "relations" in self._response_model.service_config:
            return None

        object_codes = list({getattr(r, "Code") for r in self._rows})

        relations_config = RelationsConfig.model_validate(self._response_model.service_config["relations"])

        object_types = {relation.object_type for relation in relations_config.objects}
        object_type_details = {relation.object_type: relation for relation in relations_config.objects}

        return Config(
            object_codes=object_codes,
            object_types=list(object_types),
            object_type_details=object_type_details,
        )


class AddRelationsServiceFactory:
    def create_service(
        self,
        session: Session,
        rows: List[BaseModel],
        response_model: Model,
    ) -> AddRelationsService:
        return AddRelationsService(
            session=session,
            rows=rows,
            response_model=response_model,
        )

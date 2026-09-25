from collections import defaultdict
from typing import Any, get_args

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
    objects: list[ObjectRelationConfig]


class Config(BaseModel):
    object_codes: list[str]
    object_types: list[str]
    object_type_details: dict[str, ObjectRelationConfig]


class AddRelationsService:
    def __init__(
        self,
        session: Session,
        rows: list[BaseModel],
        response_model: Model,
    ):
        self._session: Session = session
        self._rows: list[BaseModel] = rows
        self._response_model: DynamicObjectModel | Model = response_model

    def add_relations(self) -> list[BaseModel]:
        config: Config | None = self._collect_config()
        if not config:
            return self._rows

        relation_rows: list[dict[str, Any]] = self._fetch_relation_rows(config)

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
            target_code: str = relation_row["_relation_from_code"]
            if relation_row["_relation_from_code"] == relation_row["code"]:
                target_code = relation_row["_relation_to_code"]

            relation_object_type: str = relation_row["object_type"]
            object_config: ObjectRelationConfig = config.object_type_details[relation_object_type]

            # extract the created relation-object pydantic model
            field_annotation = self._response_model.pydantic_model.model_fields[object_config.to_field].annotation
            relation_row_model = get_args(field_annotation)[0]

            # Created wrapped relation model if configures with wrapped_with_relation_data
            field_value: dict = relation_row
            if object_config.wrapped_with_relation_data:
                field_value = {
                    "relation": {
                        "object_type": relation_row.get("object_type"),
                        "object_id": relation_row.get("object_id"),
                        "description": relation_row.get("_relation_description"),
                    },
                    "object": relation_row,
                }

            field_result: BaseModel = relation_row_model.model_validate(field_value)
            relations[target_code][object_config.to_field].append(field_result)

        # Now we union the relation "rows" into the event rows
        result_rows: list[BaseModel] = []
        for row in self._rows:
            if row.code in relations:
                for field_name, content in relations[row.code].items():
                    setattr(row, field_name, content)
            result_rows.append(row)

        return result_rows

    def _fetch_relation_rows(self, config: Config) -> list[dict[str, Any]]:
        subq = (
            select(
                ObjectsTable,
                RelationsTable.from_code.label("_relation_from_code"),
                RelationsTable.to_code.label("_relation_to_code"),
                RelationsTable.description.label("_relation_description"),
                func.row_number()
                .over(
                    partition_by=ObjectsTable.code,
                    order_by=desc(ObjectsTable.modified_date),
                )
                .label("_row_number"),
            )
            .select_from(RelationsTable)
            .join(
                ObjectsTable,
                or_(ObjectsTable.code == RelationsTable.from_code, ObjectsTable.code == RelationsTable.to_code),
            )
            .filter(
                or_(
                    RelationsTable.from_code.in_(config.object_codes),
                    RelationsTable.to_code.in_(config.object_codes),
                )
            )
            .filter(ObjectsTable.object_type.in_(config.object_types))
            .subquery()
        )

        stmt = select(subq).filter(subq.c._row_number == 1)

        rows = self._session.execute(stmt).all()
        dict_rows = [r._asdict() for r in rows]
        return dict_rows

    def _collect_config(self) -> Config | None:
        if not isinstance(self._response_model, DynamicObjectModel):
            return None
        if "relations" not in self._response_model.service_config:
            return None

        object_codes = list({r.code for r in self._rows})

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
        rows: list[BaseModel],
        response_model: Model,
    ) -> AddRelationsService:
        return AddRelationsService(
            session=session,
            rows=rows,
            response_model=response_model,
        )

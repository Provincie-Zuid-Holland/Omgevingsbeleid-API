from datetime import datetime
from typing import TypeVar

from sqlalchemy import func, text
from sqlalchemy.orm import DeclarativeMeta, Query, RelationshipProperty, aliased
from sqlalchemy.sql import label
from sqlalchemy.types import UserDefinedType
from sqlalchemy.util import ImmutableProperties

from app.db.base_class import NULL_UUID, Base
from app.models.beleidskeuze import Beleidskeuze


# Geo
class Geometry(UserDefinedType):
    def get_col_spec(self):
        return "geometry"

    def bind_expression(self, bindvalue):
        # Note that this does *not* format the value to the expression text, but
        # the bind value key.
        return text(
            f"Geometry::STGeomFromText(GEOMETRY::STGeomFromText(:{bindvalue.key},4269).MakeValid().STUnion(GEOMETRY::STGeomFromText(:{bindvalue.key},4269).STStartPoint()).STAsText(),4269)"
        ).bindparams(bindvalue)
        # return text(f'Geometry::STGeomFromText(:{bindvalue.key},0)').bindparams(bindvalue)


## Relationships
ModelType = TypeVar("ModelType", bound=Base)


def get_relationships(model: ModelType) -> ImmutableProperties:
    return model.__mapper__.relationships


def get_relationship_class(relation: RelationshipProperty) -> DeclarativeMeta:
    return relation.entity.class_


def get_valid_subq() -> Beleidskeuze:
    from app.models.beleidskeuze import Beleidskeuze

    # Inner query
    partition = func.row_number().over(
        partition_by=Beleidskeuze.ID, order_by=Beleidskeuze.Modified_Date.desc()
    )

    row_number = label("RowNumber", partition)

    inner_subq = (
        Query([Beleidskeuze, row_number])
        .filter(Beleidskeuze.Status == "Vigerend")
        .filter(Beleidskeuze.UUID != NULL_UUID)
        .filter(Beleidskeuze.Begin_Geldigheid <= datetime.utcnow())
    ).subquery("inner")

    inner_alias: Beleidskeuze = aliased(
        element=Beleidskeuze, alias=inner_subq, name="inner"
    )

    # Full valid query
    sub_query = (
        Query(inner_alias)
        .filter(inner_subq.c.get("RowNumber") == 1)
        .filter(inner_alias.Eind_Geldigheid > datetime.utcnow())
    ).subquery()

    # As BK alias
    valid_alias = aliased(element=Beleidskeuze, alias=sub_query, name="subq")
    return valid_alias

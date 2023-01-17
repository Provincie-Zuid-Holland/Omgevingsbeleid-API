from typing import TypeVar

from sqlalchemy import text
from sqlalchemy.orm import DeclarativeMeta, RelationshipProperty
from sqlalchemy.types import UserDefinedType
from sqlalchemy.util import ImmutableProperties

from app.db.base_class import Base


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


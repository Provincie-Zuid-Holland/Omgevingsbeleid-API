from sqlalchemy.types import UserDefinedType


class Geometry(UserDefinedType):
    def get_col_spec(self):
        return "geometry"

    def bind_expression(self, bindvalue):
        # Note that this does *not* format the value to the expression text, but
        # the bind value key.
        return text(f'Geometry::STGeomFromText(GEOMETRY::STGeomFromText(:{bindvalue.key},4269).MakeValid().STUnion(GEOMETRY::STGeomFromText(:{bindvalue.key},4269).STStartPoint()).STAsText(),4269)').bindparams(bindvalue)

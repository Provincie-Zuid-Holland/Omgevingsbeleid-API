from sqlalchemy import text
from sqlalchemy.sql.elements import BindParameter
from sqlalchemy.types import UserDefinedType


class Geometry(UserDefinedType):
    def get_col_spec(self):
        return "geometry"

    def bind_expression(self, bindvalue):
        database_type = self._get_dialect_name(bindvalue)

        if database_type == "mssql":
            return text(f"Geometry::STGeomFromText(:{bindvalue.key}, 28992)").bindparams(bindvalue)
        if database_type == "sqlite":
            return text(f"GeomFromText(:{bindvalue.key}, 28992)").bindparams(bindvalue)

        raise NotImplementedError(f"The database type '{database_type}' is not supported for Geometry type.")

    def _get_dialect_name(self, bindvalue):
        if isinstance(bindvalue, BindParameter) and bindvalue._bind:
            return bindvalue._bind.dialect.name
        elif hasattr(bindvalue, "compile") and hasattr(bindvalue.compile, "dialect"):
            return bindvalue.compile.dialect.name
        else:
            raise AttributeError("Unable to determine the database dialect from the bind value.")

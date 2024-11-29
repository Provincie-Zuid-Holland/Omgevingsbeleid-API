from sqlalchemy import text, types
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.elements import BindParameter
from sqlalchemy.sql.functions import FunctionElement
from sqlalchemy.types import UserDefinedType


class STAsBinary(FunctionElement):
    type = types.LargeBinary  # Specify the return type
    name = "STAsBinary"
    inherit_cache = True


@compiles(STAsBinary)
def compile_STAsBinary(element, compiler, **kw):
    """
    Custom SQLAlchemy compiler for STAsBinary.
    Renders output in format: [column].STAsBinary()
    """
    col = compiler.process(list(element.clauses)[0], **kw)  # Get the column expression
    return f"{col}.STAsBinary()"


class Geometry(UserDefinedType):
    cache_ok = True

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

    class comparator_factory(UserDefinedType.Comparator):
        def STAsBinary(self):
            return STAsBinary(self.expr)

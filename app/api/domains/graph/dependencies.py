from typing import Annotated, Optional

from fastapi import Depends, Request
from sqlalchemy import text

from app.api.utils.pagination import OptionalSort, OptionalSortedPagination, SimplePagination, SortOrder

from falkordb import FalkorDB, Graph


def depends_falkordb_session(request: Request) -> FalkorDB:
    return FalkorDB(host="localhost", port=6379)


def depends_api_graph(
    falkordb: Annotated[FalkorDB, Depends(depends_falkordb_session)],
) -> Graph:
    return falkordb.select_graph("api")

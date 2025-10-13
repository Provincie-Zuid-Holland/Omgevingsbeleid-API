import os
from typing import Optional

from fastapi import Request
from sqlalchemy import text

from app.api.utils.pagination import OptionalSort, OptionalSortedPagination, SimplePagination, SortOrder


def depends_db_session(request: Request):
    if os.getenv("PYTEST_ACTIVE") == "1":
        """
        A transaction is already started by the test setup, so this function should not begin a new one to avoid nesting
        """
        yield request.app.state.db_sessionmaker()
    else:
        db_sessionmaker = request.app.state.db_sessionmaker

        with db_sessionmaker.begin() as session:
            try:
                # when using SQLite, ensure FK constraints and load Spatialite
                if session.bind.dialect.name == "sqlite":
                    session.execute(text("PRAGMA foreign_keys = ON"))
                    session.execute(text("SELECT load_extension('mod_spatialite')"))
                yield session
                # commit happens automatically when exiting the 'with' block
            except Exception:
                session.rollback()
                raise


def depends_simple_pagination(
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> SimplePagination:
    return SimplePagination(offset=offset, limit=limit)


def depends_optional_sorted_pagination(
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    sort_column: Optional[str] = None,
    sort_order: Optional[SortOrder] = None,
) -> OptionalSortedPagination:
    optional_sort = OptionalSort(
        column=sort_column,
        order=sort_order,
    )
    pagination = OptionalSortedPagination(
        offset=offset,
        limit=limit,
        sort=optional_sort,
    )
    return pagination

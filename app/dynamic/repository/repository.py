from sqlalchemy import Select
from sqlalchemy.orm import Session

from app.dynamic.utils.pagination import PaginatedQueryResult, query_paginated, _query_total_count, _add_pagination


class BaseRepository:
    def __init__(self, db: Session):
        self._db = db

    def fetch_first(self, statement: Select):
        return self._db.scalars(statement).first()

    def fetch_all(self, statement: Select):
        return list(self._db.scalars(statement).all())

    def fetch_paginated(self, statement: Select, offset: int, limit: int, sort=None) -> PaginatedQueryResult:
        """
        Execute a query for paginated results with a seperate total count.
        """
        return query_paginated(query=statement, session=self._db, limit=limit, offset=offset, sort=sort)

    def fetch_paginated_no_scalars(self, statement: Select, offset: int, limit: int, sort=None) -> PaginatedQueryResult:
        """
        Same as fetch_paginated without calling scalars() on results
        to allow custom query results.
        """
        paginated = _add_pagination(statement, limit, offset, sort)
        results = self._db.execute(paginated).all()
        total_count = _query_total_count(statement, self._db)
        return PaginatedQueryResult(items=list(results), total_count=total_count)

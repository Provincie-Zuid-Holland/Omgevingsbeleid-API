from sqlalchemy import Select
from sqlalchemy.orm import Session

from app.api.utils.pagination import PaginatedQueryResult, add_pagination, query_paginated, query_total_count


class BaseRepository:
    def fetch_first(self, session: Session, statement: Select):
        return session.scalars(statement).first()

    def fetch_all(self, session: Session, statement: Select):
        return list(session.scalars(statement).all())

    def fetch_paginated(
        self, session: Session, statement: Select, offset: int, limit: int, sort=None
    ) -> PaginatedQueryResult:
        return query_paginated(query=statement, session=session, limit=limit, offset=offset, sort=sort)

    def fetch_paginated_no_scalars(
        self, session: Session, statement: Select, offset: int, limit: int, sort=None
    ) -> PaginatedQueryResult:
        """
        Same as fetch_paginated without calling scalars() on results
        to allow custom query results.
        """
        paginated = add_pagination(statement, limit, offset, sort)
        results = session.execute(paginated).all()
        total_count = query_total_count(statement, session)
        return PaginatedQueryResult(items=list(results), total_count=total_count)

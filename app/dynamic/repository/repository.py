from sqlalchemy import Select

from sqlalchemy.orm import Session
from sqlalchemy import func, select

from app.dynamic.utils.pagination import PaginatedQueryResult


class BaseRepository:
    def __init__(self, db: Session):
        self._db = db

    def fetch_first(self, statement: Select):
        return self._db.scalars(statement).first()

    def fetch_all(self, statement: Select):
        return list(self._db.scalars(statement).all())

    def fetch_paginated(
        self, statement: Select, offset: int, limit: int
    ) -> PaginatedQueryResult:
        """
        Execute a query for paginated results with a seperate total count.
        """
        # build paginated query
        paginated = statement.limit(limit).offset(offset)
        # query for getting the total count
        count_stmt = select(func.count()).select_from(statement.alias())

        # fetch results
        results = self._db.execute(paginated).scalars().all()
        total_count = self._db.execute(count_stmt).scalar_one()

        return PaginatedQueryResult(items=results, total_count=total_count)

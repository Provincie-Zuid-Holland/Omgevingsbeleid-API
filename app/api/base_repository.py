from collections.abc import AsyncIterator

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils.pagination import PaginatedQueryResult, add_pagination, query_paginated, query_total_count


class BaseRepository:
    async def fetch_first(self, session: AsyncSession, statement: Select):
        return (await session.scalars(statement)).first()

    async def fetch_all(self, session: AsyncSession, statement: Select):
        return list((await session.scalars(statement)).all())

    async def iter_all(self, session: AsyncSession, statement: Select, batch_size: int = 100) -> AsyncIterator:
        result = await session.stream_scalars(statement.execution_options(yield_per=batch_size))
        async for row in result:
            yield row

    async def fetch_paginated(
        self, session: AsyncSession, statement: Select, offset: int, limit: int, sort=None
    ) -> PaginatedQueryResult:
        return await query_paginated(query=statement, session=session, limit=limit, offset=offset, sort=sort)

    async def fetch_paginated_no_scalars(
        self, session: AsyncSession, statement: Select, offset: int, limit: int, sort=None
    ) -> PaginatedQueryResult:
        """
        Same as fetch_paginated without calling scalars() on results
        to allow custom query results.
        """
        paginated = add_pagination(statement, limit, offset, sort)
        results = (await session.execute(paginated)).all()
        total_count = await query_total_count(statement, session)
        return PaginatedQueryResult(items=list(results), total_count=total_count)

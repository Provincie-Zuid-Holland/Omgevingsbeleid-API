import asyncio
from collections.abc import Awaitable, Callable

from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.db.session import AsyncSessionFactoryType, async_session_scope


def run_with_session[T](session_factory: AsyncSessionFactoryType, handler: Callable[[AsyncSession], Awaitable[T]]) -> T:
    """Runs an async command body with one session. Click commands themselves are sync."""

    async def _run() -> T:
        try:
            async with async_session_scope(session_factory) as session:
                return await handler(session)
        finally:
            await session_factory.kw["bind"].dispose()

    return asyncio.run(_run())


def run_with_connection(engine: AsyncEngine, handler: Callable[[Connection], None]) -> None:
    """Runs sync connection work (like metadata.create_all) in one transaction on the async engine."""

    async def _run() -> None:
        try:
            async with engine.begin() as connection:
                await connection.run_sync(handler)
        finally:
            await engine.dispose()

    asyncio.run(_run())

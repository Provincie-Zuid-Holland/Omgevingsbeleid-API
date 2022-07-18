import asyncio
from typing import List

import pytest
from httpx import AsyncClient

from main import app


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def non_mocked_hosts() -> List[str]:
    return ["test"]


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client





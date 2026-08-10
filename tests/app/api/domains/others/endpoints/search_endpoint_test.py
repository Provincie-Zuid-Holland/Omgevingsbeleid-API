from typing import Any, Dict, List

from pydantic import BaseModel
from rich import print as pprint
from fastapi.testclient import TestClient

from tests.conftest import Context


class Response(BaseModel):
    total: int
    offset: int
    limit: int
    results: List[Dict[str, Any]]


def test_search(admin: TestClient, ctx: Context):
    body = admin.post(
        "/search",
        json={
            "Query": "%beleidsdoel%",
        },
    ).json()
    pprint(body)

    # a = True

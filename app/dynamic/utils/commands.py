from contextlib import AsyncExitStack
from typing import Callable, Dict

from fastapi import FastAPI, Request
from fastapi.dependencies.utils import SolvedDependency, get_dependant, solve_dependencies


async def resolve_dependencies(app: FastAPI, dependencies: Dict[str, Callable]) -> Dict[str, Callable]:
    result: Dict[str, Callable] = {}

    async with AsyncExitStack() as async_exit_stack:
        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/",
                "headers": [],
                "query_string": b"",
                "client": ("testclient", 123),
                "app": app,
                "scheme": "http",
                "server": ("testserver", 80),
            }
        )

        for key, dependency_function in dependencies.items():
            dependant = get_dependant(path="/", call=dependency_function)
            solved_dependency: SolvedDependency = await solve_dependencies(
                request=request,
                dependant=dependant,
                dependency_overrides_provider=app,
                async_exit_stack=async_exit_stack,
                embed_body_fields=False,  # needs True if requests are handled
            )
            values = solved_dependency.values

            result[key] = dependency_function(**values)

    return result

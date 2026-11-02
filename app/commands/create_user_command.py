from typing import Annotated

import click
from dependency_injector.wiring import Provide, inject
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_container import ApiContainer
from app.api.services.create_user_service import CreateUserService
from app.api.services.permission_service import PermissionService
from app.commands.async_runner import run_with_session
from app.core.db.session import AsyncSessionFactoryType


@click.command
@click.argument("email")
@click.argument("name")
@click.password_option(required=True)
@click.argument("roles", nargs=-1, required=True)
@inject
def create_user(
    db_session_factory: Annotated[AsyncSessionFactoryType, Provide[ApiContainer.db_session_factory]],
    create_user_service: Annotated[CreateUserService, Provide[ApiContainer.create_user_service]],
    permission_service: Annotated[PermissionService, Provide[ApiContainer.permission_service]],
    email: str,
    name: str,
    password: str | None,
    roles: tuple[str, ...],
):
    if password is None:
        raise ValueError("password is required")

    async def _do(session: AsyncSession) -> None:
        _ = await create_user_service.create_user(
            session,
            name,
            email,
            password,
            set(roles),
            permission_service.get_known_permissions(),
        )

        await session.commit()
        click.echo("User created")

    run_with_session(db_session_factory, _do)

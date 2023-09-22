import uuid
from typing import Optional

import click
from sqlalchemy import select

from app.core.dependencies import db_in_context_manager
from app.core.security import get_password_hash, get_random_password
from app.extensions.users.db.tables import IS_ACTIVE, UsersTable


@click.command()
@click.argument("gebruikersnaam")
@click.argument("email")
@click.argument("rol")
def create_user(gebruikersnaam, email, rol):
    password = "change-me-" + get_random_password()
    password_hash = get_password_hash(password)

    user: UsersTable = UsersTable(
        UUID=uuid.uuid4(),
        Gebruikersnaam=gebruikersnaam,
        Email=email,
        Rol=rol,
        Status=IS_ACTIVE,
        Wachtwoord=password_hash,
    )

    with db_in_context_manager() as db:
        db.add(user)
        db.flush()
        db.commit()

        click.echo("")
        click.echo(f"User created with password: {password}")
        click.echo("")


@click.command()
@click.argument("email")
def reset_password(email):
    password = "change-me-" + get_random_password()
    password_hash = get_password_hash(password)

    with db_in_context_manager() as db:
        stmt = select(UsersTable).filter(UsersTable.Email == email)
        user: Optional[UsersTable] = db.scalars(stmt).first()
        if not user:
            click.echo("Email not found")
            raise Exception("Email not found")

        user.Wachtwoord = password_hash
        db.flush()
        db.commit()

        click.echo("")
        click.echo(f"User password changed: {password}")
        click.echo("")


@click.command()
@click.argument("uuid")
def reset_password_uuid(uuid):
    password = "change-me-" + get_random_password()
    password_hash = get_password_hash(password)

    with db_in_context_manager() as db:
        stmt = select(UsersTable).filter(UsersTable.UUID == uuid)
        user: Optional[UsersTable] = db.scalars(stmt).first()
        if not user:
            click.echo("UUID not found")
            raise Exception("UUID not found")

        user.Wachtwoord = password_hash
        db.flush()
        db.commit()

        click.echo("")
        click.echo(f"User password changed: {password}")
        click.echo(f"User email: {user.Email}")
        click.echo("")

import random
import string
import uuid
from typing import Optional

import click
from sqlalchemy import select

from app.core.dependencies import db_in_context_manager
from app.core.security import get_password_hash
from app.extensions.users.db.tables import UsersTable


@click.command()
@click.argument("gebruikersnaam")
@click.argument("email")
@click.argument("rol")
def create_user(gebruikersnaam, email, rol):
    password = "change-me-" + get_random_password(8)
    password_hash = get_password_hash(password)

    user: UsersTable = UsersTable(
        UUID=uuid.uuid4(),
        Gebruikersnaam=gebruikersnaam,
        Email=email,
        Rol=rol,
        Status="Actief",
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
    password = "change-me-" + get_random_password(8)
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


def get_random_password(length: int = 16):
    password = "".join(random.choice(string.ascii_letters) for i in range(length))
    return password

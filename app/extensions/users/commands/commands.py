import random
import string
import uuid

import click

from app.core.dependencies import db_in_context_manager
from app.core.security import get_password_hash
from app.extensions.users.db.tables import UsersTable


@click.command()
@click.argument("gebruikersnaam")
@click.argument("email")
@click.argument("rol")
def create_user(gebruikersnaam, email, rol):
    password = "change-me" + get_random_password(5)
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


def get_random_password(length: int = 16):
    password = "".join(random.choice(string.ascii_letters) for i in range(length))
    return password

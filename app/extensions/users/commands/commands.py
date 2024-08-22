import uuid
from typing import Optional

import click
from sqlalchemy import select, text

from app.core.dependencies import db_in_context_manager
from app.core.security import Security
from app.core.settings.dynamic_settings import DynamicSettings, create_dynamic_settings
from app.extensions.users.db.tables import IS_ACTIVE, UsersTable


def get_security() -> Security:
    settings: DynamicSettings = create_dynamic_settings()
    return Security(settings)


@click.command()
@click.argument("gebruikersnaam")
@click.argument("email")
@click.argument("rol")
def create_user(gebruikersnaam, email, rol):
    security: Security = get_security()
    password = "change-me-" + security.get_random_password()
    password_hash = security.get_password_hash(password)

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
    security: Security = get_security()
    password = "change-me-" + security.get_random_password()
    password_hash = security.get_password_hash(password)

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
    security: Security = get_security()
    password = "change-me-" + security.get_random_password()
    password_hash = security.get_password_hash(password)

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


@click.command()
@click.argument("from_uuid")
@click.argument("to_uuid")
@click.option("--include-legacy", is_flag=True, help="Include legacy tables like Onderverdelingen.")
def change_user_actions_to(from_uuid, to_uuid, include_legacy):
    print("from:")
    print(from_uuid)
    print("to:")
    print(to_uuid)
    try:
        from_uuid = str(uuid.UUID(from_uuid))
        to_uuid = str(uuid.UUID(to_uuid))
    except ValueError as e:
        print(e)
        click.echo("Invalid UUID")
        raise click.Abort()

    print("from:")
    print(from_uuid)
    print("to:")
    print(to_uuid)

    with db_in_context_manager() as db:
        from_user: Optional[UsersTable] = db.scalars(
            select(UsersTable).filter(UsersTable.UUID == uuid.UUID(from_uuid))
        ).first()
        if not from_user:
            click.echo("From user not found")
            raise click.Abort()
        to_user: Optional[UsersTable] = db.scalars(
            select(UsersTable).filter(UsersTable.UUID == uuid.UUID(to_uuid))
        ).first()
        if not to_user:
            click.echo("To user not found")
            raise click.Abort()

        statements = [
            # objects
            f"UPDATE objects SET Created_By_UUID = :to_uuid WHERE Created_By_UUID = :from_uuid",
            f"UPDATE objects SET Modified_By_UUID = :to_uuid WHERE Modified_By_UUID = :from_uuid",
            # object_statics
            f"UPDATE object_statics SET Owner_1_UUID = :to_uuid WHERE Owner_1_UUID = :from_uuid",
            f"UPDATE object_statics SET Owner_2_UUID = :to_uuid WHERE Owner_2_UUID = :from_uuid",
            f"UPDATE object_statics SET Portfolio_Holder_1_UUID = :to_uuid WHERE Portfolio_Holder_1_UUID = :from_uuid",
            f"UPDATE object_statics SET Portfolio_Holder_2_UUID = :to_uuid WHERE Portfolio_Holder_2_UUID = :from_uuid",
            f"UPDATE object_statics SET Client_1_UUID = :to_uuid WHERE Client_1_UUID = :from_uuid",
            f"UPDATE object_statics SET Owner_2_UUID = NULL WHERE Owner_1_UUID = :to_uuid AND Owner_2_UUID = :to_uuid",
            f"UPDATE object_statics SET Portfolio_Holder_2_UUID = NULL WHERE Portfolio_Holder_1_UUID = :to_uuid AND Portfolio_Holder_2_UUID = :to_uuid",
            # modules
            f"UPDATE modules SET Created_By_UUID = :to_uuid WHERE Created_By_UUID = :from_uuid",
            f"UPDATE modules SET Modified_By_UUID = :to_uuid WHERE Modified_By_UUID = :from_uuid",
            f"UPDATE modules SET Module_Manager_1_UUID = :to_uuid WHERE Module_Manager_1_UUID = :from_uuid",
            f"UPDATE modules SET Module_Manager_2_UUID = :to_uuid WHERE Module_Manager_2_UUID = :from_uuid",
            f"UPDATE modules SET Module_Manager_2_UUID = NULL WHERE Module_Manager_1_UUID = :to_uuid AND Module_Manager_2_UUID = :to_uuid",
            # module_status_history
            f"UPDATE module_status_history SET Created_By_UUID = :to_uuid WHERE Created_By_UUID = :from_uuid",
            # module_objects
            f"UPDATE module_objects SET Created_By_UUID = :to_uuid WHERE Created_By_UUID = :from_uuid",
            f"UPDATE module_objects SET Modified_By_UUID = :to_uuid WHERE Modified_By_UUID = :from_uuid",
            # module_object_context
            f"UPDATE module_object_context SET Created_By_UUID = :to_uuid WHERE Created_By_UUID = :from_uuid",
            f"UPDATE module_object_context SET Modified_By_UUID = :to_uuid WHERE Modified_By_UUID = :from_uuid",
            # change_log
            f"UPDATE change_log SET Created_By_UUID = :to_uuid WHERE Created_By_UUID = :from_uuid",
            # assets
            f"UPDATE assets SET Created_By_UUID = :to_uuid WHERE Created_By_UUID = :from_uuid",
            # acknowledged_relations
            f"UPDATE acknowledged_relations SET Created_By_UUID = :to_uuid WHERE Created_By_UUID = :from_uuid",
            f"UPDATE acknowledged_relations SET Modified_By_UUID = :to_uuid WHERE Modified_By_UUID = :from_uuid",
            f"UPDATE acknowledged_relations SET From_Acknowledged_By_UUID = :to_uuid WHERE From_Acknowledged_By_UUID = :from_uuid",
            f"UPDATE acknowledged_relations SET To_Acknowledged_By_UUID = :to_uuid WHERE To_Acknowledged_By_UUID = :from_uuid",
        ]
        if include_legacy:
            statements = statements + [
                # Werkingsgebieden
                f"UPDATE Werkingsgebieden SET Created_By = :to_uuid WHERE Created_By = :from_uuid",
                f"UPDATE Werkingsgebieden SET Modified_By = :to_uuid WHERE Modified_By = :from_uuid",
                # Verordeningstructuur
                f"UPDATE Verordeningstructuur SET Created_By = :to_uuid WHERE Created_By = :from_uuid",
                f"UPDATE Verordeningstructuur SET Modified_By = :to_uuid WHERE Modified_By = :from_uuid",
                # Verordeningen
                f"UPDATE Verordeningen SET Created_By = :to_uuid WHERE Created_By = :from_uuid",
                f"UPDATE Verordeningen SET Modified_By = :to_uuid WHERE Modified_By = :from_uuid",
                f"UPDATE Verordeningen SET Portefeuillehouder_1 = :to_uuid WHERE Portefeuillehouder_1 = :from_uuid",
                f"UPDATE Verordeningen SET Portefeuillehouder_2 = :to_uuid WHERE Portefeuillehouder_2 = :from_uuid",
                f"UPDATE Verordeningen SET Eigenaar_1 = :to_uuid WHERE Eigenaar_1 = :from_uuid",
                f"UPDATE Verordeningen SET Eigenaar_2 = :to_uuid WHERE Eigenaar_2 = :from_uuid",
                f"UPDATE Verordeningen SET Portefeuillehouder_2 = NULL WHERE Portefeuillehouder_1 = :to_uuid AND Portefeuillehouder_2 = :to_uuid",
                f"UPDATE Verordeningen SET Eigenaar_2 = NULL WHERE Eigenaar_1 = :to_uuid AND Eigenaar_2 = :to_uuid",
                # Onderverdeling
                f"UPDATE Onderverdeling SET Created_By = :to_uuid WHERE Created_By = :from_uuid",
                f"UPDATE Onderverdeling SET Modified_By = :to_uuid WHERE Modified_By = :from_uuid",
            ]

        for stmt in statements:
            db.execute(text(stmt), {"to_uuid": to_uuid, "from_uuid": from_uuid})

        db.flush()
        db.commit()

    click.echo("Done")


@click.command()
@click.argument("uuid")
@click.option("--yes", is_flag=True, help="Just a little extra you have to do, so you do not call this by mistake")
def delete_user_uuid(uuid, yes):
    if not yes:
        click.echo("You have to add --yes")
        raise click.Abort()
    with db_in_context_manager() as db:
        stmt = select(UsersTable).filter(UsersTable.UUID == uuid)
        user: Optional[UsersTable] = db.scalars(stmt).first()
        if not user:
            click.echo("UUID not found")
            raise Exception("UUID not found")

        click.echo("\n")
        click.echo("Deleting user")
        click.echo(f"User uuid: {user.UUID}")
        click.echo(f"User email: {user.Email}")
        click.echo("\n")

        db.delete(user)
        db.flush()
        db.commit()

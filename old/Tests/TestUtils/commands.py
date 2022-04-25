# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

import click
from flask.cli import with_appcontext
from flask import current_app
from passlib.hash import bcrypt

from Api.Models.gebruikers import Gebruikers
from Tests.TestUtils.data_loader import FixtureLoader


@click.command(name="load-fixtures")
@with_appcontext
def load_fixtures(**kwargs):
    loader = FixtureLoader(current_app.db)
    loader.load_fixtures()


# Example usage: docker-compose exec api flask add-user --id 1 --gebruikersnaam alex --wachtwoord lol --rol test --email alex@pzh.nl
@click.command(name="add-user")
@click.option("--id", is_flag=False, required=True)
@click.option("--gebruikersnaam", is_flag=False, required=True)
@click.option("--wachtwoord", is_flag=False, required=True)
@click.option("--rol", is_flag=False, required=True)
@click.option("--email", is_flag=False, required=True)
@with_appcontext
def add_user(**kwargs):
    hashed_pw = bcrypt.hash(kwargs["wachtwoord"])
    new_user = Gebruikers(
        ID=kwargs["id"],
        Gebruikersnaam=kwargs["gebruikersnaam"],
        Wachtwoord=hashed_pw,
        Rol=kwargs["rol"],
        Email=kwargs["email"],
    )

    session = current_app.db.session
    session.add(new_user)
    session.commit()

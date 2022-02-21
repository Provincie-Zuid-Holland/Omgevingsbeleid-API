import click
import os
from flask.cli import FlaskGroup, ScriptInfo, with_appcontext

import Api.datamodel


# DATABASE VIEWS
@click.command(name='setup-views')
@click.option('-y', '--auto-yes', is_flag=True)
@with_appcontext
def setup_views(auto_yes):
    if auto_yes or (input(f"Working on {os.getenv('DB_NAME')}, continue?") == "y"):
        print("Setting up database views")
        for schema in Api.datamodel.endpoints:
            print(f"Updating views for {schema.Meta.slug}...")
            schema.Meta.manager(schema)._setup_views()
        print("Done updating views")
    else:
        print("exiting..")


@click.command(name='datamodel-markdown')
@with_appcontext
def dm_markdown():
    with open("./../datamodel.md", "w") as mdfile:
        mdfile.write(datamodel.generate_markdown_view())


# TEST: docker-compose exec api flask add-user --id 1 --gebruikersnaam alex --wachtwoord lol --rol test --email alex@pzh.nl
@click.command(name='add-user')
@click.option('--id', is_flag=False,required=True)
@click.option('--gebruikersnaam', is_flag=False,required=True)
@click.option('--wachtwoord', is_flag=False,required=True)
@click.option('--rol', is_flag=False,required=True)
@click.option('--email', is_flag=False,required=True)
@with_appcontext
def add_user(**kwargs):
    create_user_encrypt_pw(kwargs['id'], kwargs['gebruikersnaam'], kwargs['wachtwoord'], kwargs['rol'], kwargs['email'])

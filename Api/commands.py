import click
import os
from flask.cli import FlaskGroup, ScriptInfo, with_appcontext

import Api.datamodel


@click.command(name="setup-views")
@click.option("-y", "--auto-yes", is_flag=True)
@with_appcontext
def setup_views(auto_yes):
    if auto_yes or (input(f"Working on {os.getenv('DB_NAME')}, continue?") == "y"):
        print("Setting up database views")
        Api.datamodel.setup_views()
        print("Done updating views")
    else:
        print("exiting..")


@click.command(name="datamodel-markdown")
@with_appcontext
def dm_markdown():
    with open("./../datamodel.md", "w") as mdfile:
        mdfile.write(datamodel.generate_markdown_view())


@click.command(name="datamodel-dbdiagram")
@with_appcontext
def dm_dbdiagram():
    datamodel.generate_dbdiagram()

import click
import os
from flask.cli import FlaskGroup, ScriptInfo, with_appcontext
from flask import current_app
import pyodbc
from typing import DefaultDict

import Api.datamodel
from Api.settings import null_uuid


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


@click.command(name="database-test-nills")
@with_appcontext
def database_test_nills():
    """Check wether all the tables in the datamodel contain a Nill UUID"""
    print("\n")
    error_count = 0
    with pyodbc.connect(current_app.config['DB_CONNECTION_SETTINGS']) as connections:
        cur = connections.cursor()
        for ep in Api.datamodel.endpoints:
            query = f"SELECT UUID FROM {ep.Meta.table} WHERE UUID = ?"
            cur.execute(query, null_uuid)
            results = cur.fetchall()
            if len(results) != 1:
                print(f"No Nill UUID object in table {ep.Meta.slug}")
                error_count += 1
    print(f"\nTotal errors: {error_count}\n")
    return error_count


# @todo: is this still working or was this already deprecated?
@click.command(name="database-test-search-index")
@with_appcontext
def database_test_search_index():
    """Check wether all the tables are properly configured for search"""
    with pyodbc.connect(current_app.config['DB_CONNECTION_SETTINGS']) as connections:
        cur = connections.cursor()
        query = f"""SELECT DISTINCT OBJECT_NAME(fic.object_id) AS table_name, c.name AS column_name
                    FROM sys.fulltext_index_columns AS fic INNER JOIN
                    sys.columns AS c ON c.object_id = fic.object_id AND c.column_id = fic.column_id"""
        cur.execute(query)
        fieldmap = DefaultDict(list)
        for table, field in cur.fetchall():
            fieldmap[table].append(field)
        for ep in Api.datamodel.endpoints:
            search_fields = ep.fields_with_props(["search_title"]) + ep.fields_with_props(["search_description"])
            assert set(fieldmap[ep.Meta.table]) == set(search_fields), f"Search configuration not matching database state for {ep.Meta.slug}"

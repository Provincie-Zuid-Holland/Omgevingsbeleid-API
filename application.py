# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2020 Provincie Zuid-Holland

from Endpoints.data_manager import DataManager
import json
import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required
from flask_restful import Api, Resource
from flask_migrate import Migrate
from Endpoints.edits import editView
from Models import gebruikers, verordeningsstructuur, beleidskeuzes, maatregelen, onderverdeling
import datamodel
import Endpoints.endpoint
from Auth.views import jwt_required_not_GET, login, password_reset, tokenstat
from Spec.spec import specView
from Endpoints.search import search_view
from Endpoints.graph import graphView
from Endpoints.geo_search import geo_search_view
import click
from db import db
import globals

current_version = "0.1"

# ENV SETUP
load_dotenv()

# FLASK SETUP
app = Flask(__name__)
CORS(app)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=4)
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = globals.sqlalchemy_database_uri
api = Api(
    app,
    prefix=f"/v{current_version}",
    decorators=[
        jwt_required_not_GET,
    ],
)
jwt = JWTManager(app)

db.init_app(app)
migrate = Migrate(app, db)

# DATABASE SETUP
@app.cli.command("setup-views")
def setup_db():
    if input(f"Working on {os.getenv('DB_NAME')}, continue?") == "y":
        print("Setting up database views")
        for schema in datamodel.endpoints:
            print(f"Updating views for {schema.Meta.slug}...")
            schema.Meta.manager(schema)._setup_views()
        print("Done updating views")
    else:
        print("exiting..")

# @depricated
@app.cli.command("setup-database")
def setup_db():
    if input(f"Working on {os.getenv('DB_NAME')}, continue?") == "y":
        print("Setting up database tables")
        for schema in datamodel.endpoints:
            print(f"Creating table for {schema.Meta.slug}...")
            schema.Meta.manager(schema)._setup_table()
        print("Done creating table")
    else:
        print("exiting..")

@app.cli.command("setup-tables")
def setup_tables():
    print("Hi")
    print(db)
    from Models.ambities import Ambities_DB_Schema
    print(db.metadata.tables)
    

@app.cli.command("datamodel-markdown")
def dm_markdown():
    with open("./datamodel.md", "w") as mdfile:
        mdfile.write(datamodel.generate_markdown_view())


# JWT CONFIG
@jwt.unauthorized_loader
def custom_unauthorized_loader(reason):
    return jsonify({"message": f"Authorisatie niet geldig: '{reason}'"}), 401


# ROUTING RULES
for schema in datamodel.endpoints:
    api.add_resource(
        Endpoints.endpoint.Lineage,
        f"/{schema.Meta.slug}/<int:id>",
        endpoint=f"{schema.Meta.slug.capitalize()}_Lineage",
        resource_class_args=(schema,),
    )

    api.add_resource(
        Endpoints.endpoint.FullList,
        f"/{schema.Meta.slug}",
        endpoint=f"{schema.Meta.slug.capitalize()}_List",
        resource_class_args=(schema,),
    )

    api.add_resource(
        Endpoints.endpoint.ValidList,
        f"/valid/{schema.Meta.slug}",
        endpoint=f"{schema.Meta.slug.capitalize()}_Validlist",
        resource_class_args=(schema,),
    )

    api.add_resource(
        Endpoints.endpoint.ValidLineage,
        f"/valid/{schema.Meta.slug}/<int:id>",
        endpoint=f"{schema.Meta.slug.capitalize()}_Validlineage",
        resource_class_args=(schema,),
    )

    api.add_resource(
        Endpoints.endpoint.SingleVersion,
        f"/version/{schema.Meta.slug}/<string:uuid>",
        endpoint=f"{schema.Meta.slug.capitalize()}_Version",
        resource_class_args=(schema,),
    )

    api.add_resource(
        Endpoints.endpoint.Changes,
        f"/changes/{schema.Meta.slug}/<string:old_uuid>/<string:new_uuid>",
        endpoint=f"{schema.Meta.slug.capitalize()}_Changes",
        resource_class_args=(schema,),
    )


app.add_url_rule(f"/v{current_version}/login", "login", login, methods=["POST"])

app.add_url_rule(
    f"/v{current_version}/password-reset",
    "password-reset",
    password_reset,
    methods=["POST"],
)

app.add_url_rule(
    f"/v{current_version}/tokeninfo", "tokenstat", tokenstat, methods=["GET"]
)
api.add_resource(
    gebruikers.Gebruiker, "/gebruikers", "/gebruikers/<string:gebruiker_uuid>"
)
api.add_resource(
    verordeningsstructuur.Verordening_Structuur,
    "/verordeningstructuur",
    "/verordeningstructuur/<int:verordeningstructuur_id>",
    "/verordeningstructuur/version/<uuid:verordeningstructuur_uuid>",
)
app.add_url_rule(f"/v{current_version}/spec", "spec", specView, methods=["GET"])

app.add_url_rule(f"/v{current_version}/search", "search", search_view, methods=["GET"])

api.add_resource(
    editView,
    f"/edits",
    endpoint="edits",
    resource_class_args=(
        [beleidskeuzes.Beleidskeuzes_Schema, maatregelen.Maatregelen_Schema],
    ),
)


app.add_url_rule(
    f"/v{current_version}/search/geo", "geo-search", geo_search_view, methods=["GET"]
)

app.add_url_rule(f"/v{current_version}/graph", "graph", graphView, methods=["GET"])

app.add_url_rule(
    f"/v{current_version}/ts_defs",
    "ts_defs",
    datamodel.generate_typescript_defs,
    methods=["GET"],
)


if __name__ == "__main__":
    app.run()

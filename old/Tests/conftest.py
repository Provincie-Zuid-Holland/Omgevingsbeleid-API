# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

import pytest
from flask_jwt_extended import create_access_token
import time

from Api.application import create_app
from Api.database import db as _db
from Api.settings import TestConfig
from Api.Models.gebruikers import Gebruikers
from Api.datamodel import setup_views

from Tests.TestUtils.data_loader import FixtureLoader
from Tests.TestUtils.client import LoggedInClient


@pytest.fixture(scope="class")
def app():
    _app = create_app(TestConfig)

    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.yield_fixture(scope="class")
def db(app):

    with app.app_context():
        _db.drop_all()  # @todo: should not be here, but im lazy
        _db.create_all()
        setup_views()

    _db._app = app

    yield _db

    _db.session.close()
    # _db.drop_all() # @todo: should be here but i want to see the database in my gui


# With scope="class" this fixture will only be loaded once per class instead of for each test function
@pytest.fixture(scope="class")
def fixture_data(db):
    loader = FixtureLoader(db)
    loader.load_fixtures()

    yield loader


@pytest.fixture(scope="class")
def wait_for_fulltext_index(fixture_data, db):
    max_wait = 60
    count = 0

    query = """
        SELECT
            FULLTEXTCATALOGPROPERTY(cat.name,'PopulateStatus')
        FROM
            sys.fulltext_catalogs AS cat
        """

    while count < max_wait: 
        count += 1

        res = db.engine.execute(query)
        for row in res:
            # We are waiting untill PopulateStatus is 0, which means that the search index is updates
            if row[0] == 0:
                print(f"Search index is updated after {count-1} seconds")
                return

            time.sleep(1)
            print(f"Waiting for the search index to update {count}/{max_wait} ...")


@pytest.fixture(scope="class")
def client(app):
    """
    Provides access to the flask test_client
    """
    return app.test_client()


@pytest.fixture(scope="class")
def client_admin(db, fixture_data, app):
    return __create_client(app, db, "admin@example.com")


@pytest.fixture(scope="class")
def client_fred(db, fixture_data, app):
    return __create_client(app, db, "fred@example.com")


def __create_client(app, db, email):
    """
    Create a client which already has a jwt token for user matching given email
    """
    gebruiker = db.session.query(Gebruikers).filter(
        Gebruikers.Email == email).first()
    assert gebruiker != None, f"This user should exist"

    access_token = create_access_token(identity=gebruiker.as_identity())

    # this will force our wrapped test client
    default_class = app.test_client_class
    app.test_client_class = LoggedInClient
    client = app.test_client(gebruiker=gebruiker, access_token=access_token)

    # put the default class back for next invocations without gebruiker
    app.test_client_class = default_class

    return client

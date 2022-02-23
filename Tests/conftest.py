import pytest
from flask_jwt_extended import create_access_token

from Api.application import create_app
from Api.database import db as _db
from Api.settings import TestConfig
from Api.Models.gebruikers import Gebruikers

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
        _db.drop_all() # @todo: should not be here, but im lazy
        _db.create_all()

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
def client(fixture_data, app):
    """
    Provides access to the flask test_client

    We intentionally get fixture_data in here to fill the database
    As a client will almost always be used in combination with data
    """
    return app.test_client()


@pytest.fixture(scope="class")
def client_admin(db, fixture_data, app):
    """
    This is a client which already has a jwt token for `admin@example.com`
    """

    gebruiker = db.session.query(Gebruikers).filter(Gebruikers.Email == "admin@example.com").first()
    assert gebruiker != None, f"This user should exist"

    access_token = create_access_token(identity=gebruiker.as_identity())

    # this will force our wrapped test client
    app.test_client_class = LoggedInClient

    return app.test_client(gebruiker=gebruiker, access_token=access_token)
